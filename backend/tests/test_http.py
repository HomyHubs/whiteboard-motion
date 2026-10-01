import threading,unittest,urllib.error,urllib.request
from unittest.mock import patch
from backend.net import HttpClient,RetryPolicy,RequestCancelled
class Response:
 status=200
 def __init__(self,body=b'ok'):self.body=body;self.headers={'Content-Length':str(len(body))}
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,size=-1):body,self.body=self.body,b'';return body
class HttpTests(unittest.TestCase):
 def test_retry_then_success(self):
  calls=[];client=HttpClient(RetryPolicy(3,0,0,0),sleep=lambda x:None)
  def open_(*a,**k):
   calls.append(1)
   if len(calls)<3:raise urllib.error.URLError('temporary')
   return Response()
  with patch('urllib.request.urlopen',side_effect=open_):response=client.request(urllib.request.Request('https://example.invalid'))
  self.assertEqual(response.body,b'ok');self.assertEqual(len(calls),3)
 def test_cancel_before_request(self):
  event=threading.Event();event.set()
  with self.assertRaises(RequestCancelled):HttpClient().request(urllib.request.Request('https://example.invalid'),cancel_event=event)
