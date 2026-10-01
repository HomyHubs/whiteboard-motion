from __future__ import annotations
from dataclasses import dataclass
import json,re
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class PromptEnhancerResult:
    rewritten_prompt:str
    wh_ratio:str=''
    ratio_follow:str=''
    thinking:str=''
    parse_ok:bool=True

def _balanced_objects(text:str)->list[str]:
    spans=[];depth=0;start=-1;quoted=False;escaped=False
    for i,ch in enumerate(text):
        if quoted:
            if escaped:escaped=False
            elif ch=='\\':escaped=True
            elif ch=='"':quoted=False
            continue
        if ch=='"':quoted=True
        elif ch=='{':
            if depth==0:start=i
            depth+=1
        elif ch=='}' and depth:
            depth-=1
            if depth==0:spans.append(text[start:i+1])
    return spans

def parse_enhancer_answer(text:str,task:str)->PromptEnhancerResult:
    thinking='';answer=text.strip()
    if '</think>' in answer:thinking,answer=answer.split('</think>',1);thinking=thinking.replace('<think>','').strip();answer=answer.strip()
    for candidate in reversed(_balanced_objects(answer)):
        try:obj=json.loads(candidate)
        except json.JSONDecodeError:continue
        prompt=obj.get('rewritten_prompt') or obj.get('rewrited_prompt')
        if isinstance(prompt,str) and prompt.strip():return PromptEnhancerResult(prompt.strip(),str(obj.get('wh_ratio') or ''),str(obj.get('ratio_follow') or '') if task=='edit' else '',thinking,True)
    return PromptEnhancerResult(answer,thinking=thinking,parse_ok=False)

class PromptEnhancer:
    PROFILES={'t2i':{'presence_penalty':1.5,'max_new_tokens':16256},'edit':{'presence_penalty':0.0,'max_new_tokens':24000}}
    def __init__(self,model_path:Path,task:str='t2i',device_map:str='auto',dtype:str='bfloat16'):
        if task not in self.PROFILES:raise ValueError('task must be t2i or edit')
        self.model_path,self.task,self.device_map,self.dtype=model_path,task,device_map,dtype;self._processor=None;self._model=None
    def load(self)->None:
        if self._model is not None:return
        try:
            import torch
            from transformers import AutoModelForImageTextToText,AutoProcessor
        except ImportError as exc:raise RuntimeError('Prompt enhancer requires pinned torch/transformers runtime') from exc
        dtype={'bfloat16':torch.bfloat16,'float16':torch.float16,'float32':torch.float32}[self.dtype]
        self._processor=AutoProcessor.from_pretrained(str(self.model_path),local_files_only=True)
        self._model=AutoModelForImageTextToText.from_pretrained(str(self.model_path),dtype=dtype,low_cpu_mem_usage=True,device_map=self.device_map,local_files_only=True).eval()
    def enhance(self,prompt:str,input_images:list[Path]|None=None,seed:int=42)->PromptEnhancerResult:
        images=input_images or []
        if self.task=='t2i' and images:raise ValueError('t2i enhancer does not take images')
        if self.task=='edit' and not images:raise ValueError('edit enhancer requires at least one image')
        self.load();import torch
        system=(self.model_path/'system_prompt.txt').read_text(encoding='utf-8').strip();content=[]
        from PIL import Image
        for path in images:
            image=Image.open(path).convert('RGB');image.thumbnail((1024,1024));content.append({'type':'image','image':image})
        content.append({'type':'text','text':prompt});messages=[{'role':'system','content':[{'type':'text','text':system}]},{'role':'user','content':content}]
        inputs=self._processor.apply_chat_template(messages,add_generation_prompt=True,tokenize=True,return_dict=True,return_tensors='pt',enable_thinking=True).to(self._model.device)
        if 'mm_token_type_ids' not in inputs and hasattr(self._processor,'create_mm_token_type_ids'):inputs['mm_token_type_ids']=self._processor.create_mm_token_type_ids(inputs['input_ids'])
        prompt_len=inputs['input_ids'].shape[1];torch.manual_seed(seed);profile=self.PROFILES[self.task]
        from transformers import LogitsProcessor,LogitsProcessorList
        class PresencePenalty(LogitsProcessor):
            def __init__(self,penalty:float,start:int):self.penalty,self.start=penalty,start
            def __call__(self,input_ids,scores):
                if not self.penalty:return scores
                for batch in range(input_ids.shape[0]):
                    generated=input_ids[batch,self.start:]
                    if generated.numel():scores[batch,generated.unique()]-=self.penalty
                return scores
        processors=LogitsProcessorList([PresencePenalty(profile['presence_penalty'],prompt_len)])
        output=self._model.generate(**inputs,max_new_tokens=profile['max_new_tokens'],do_sample=True,temperature=1.0,top_p=.95,top_k=20,logits_processor=processors,pad_token_id=self._processor.tokenizer.eos_token_id)
        text=self._processor.tokenizer.decode(output[0,prompt_len:],skip_special_tokens=True)
        return parse_enhancer_answer(text,self.task)
    def unload(self)->None:
        self._model=None;self._processor=None
        try:
            import torch
            if torch.cuda.is_available():torch.cuda.empty_cache()
        except ImportError:pass
