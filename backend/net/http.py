from __future__ import annotations
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
import json,random,socket,threading,time,urllib.error,urllib.request
from typing import Callable

class RequestCancelled(RuntimeError):pass
@dataclass(frozen=True)
class RetryPolicy:
    max_attempts:int=4;base_delay_s:float=.5;max_delay_s:float=8.0;jitter:float=.15
    retry_statuses:tuple[int,...]=(408,409,425,429,500,502,503,504)
@dataclass(frozen=True)
class HttpResponse:
    status:int;headers:dict[str,str];body:bytes
    def json(self):return json.loads(self.body)
Progress=Callable[[str,float|None,str],None]

class HttpClient:
    def __init__(self,policy:RetryPolicy|None=None,sleep:Callable[[float],None]=time.sleep):self.policy=policy or RetryPolicy();self.sleep=sleep
    def _cancel(self,event:threading.Event|None):
        if event and event.is_set():raise RequestCancelled('Request cancelled')
    def _delay(self,attempt:int,headers=None)->float:
        value=headers.get('Retry-After') if headers else None
        if value:
            try:return min(self.policy.max_delay_s,max(0,float(value)))
            except ValueError:
                try:return min(self.policy.max_delay_s,max(0,(parsedate_to_datetime(value)-parsedate_to_datetime(headers.get('Date'))).total_seconds()))
                except Exception:pass
        base=min(self.policy.max_delay_s,self.policy.base_delay_s*(2**(attempt-1)));return max(0,base*(1+random.uniform(-self.policy.jitter,self.policy.jitter)))
    def _wait(self,seconds:float,event:threading.Event|None):
        if event:
            if event.wait(seconds):raise RequestCancelled('Request cancelled during backoff')
        else:self.sleep(seconds)
    def request(self,request:urllib.request.Request,timeout:float=300,cancel_event:threading.Event|None=None,progress:Progress|None=None)->HttpResponse:
        last=None
        for attempt in range(1,self.policy.max_attempts+1):
            self._cancel(cancel_event)
            if progress:progress('request',None,f'Attempt {attempt}/{self.policy.max_attempts}')
            try:
                with urllib.request.urlopen(request,timeout=timeout) as response:
                    total=int(response.headers.get('Content-Length') or 0);chunks=[];read=0
                    while True:
                        self._cancel(cancel_event);chunk=response.read(1024*1024)
                        if not chunk:break
                        chunks.append(chunk);read+=len(chunk)
                        if progress:progress('download',read/total if total else None,f'{read} bytes')
                    return HttpResponse(getattr(response,'status',200),dict(response.headers.items()),b''.join(chunks))
            except urllib.error.HTTPError as exc:
                last=exc
                if exc.code not in self.policy.retry_statuses or attempt>=self.policy.max_attempts:raise
                delay=self._delay(attempt,exc.headers)
            except (urllib.error.URLError,socket.timeout,TimeoutError) as exc:
                last=exc
                if attempt>=self.policy.max_attempts:raise
                delay=self._delay(attempt)
            if progress:progress('backoff',None,f'Retry in {delay:.2f}s')
            self._wait(delay,cancel_event)
        raise RuntimeError(f'HTTP request failed: {last}')
