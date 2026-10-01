import {useEffect,useState} from 'react';
const API='http://127.0.0.1:8765';
type Job={id:string;kind:string;status:string;progress:number;message:string;uses_gpu:boolean};
async function json(path:string,init?:RequestInit){const r=await fetch(API+path,init);if(!r.ok)throw new Error(await r.text());return r.json()}
export default function App(){
 const [connected,setConnected]=useState(false),[hardware,setHardware]=useState<any>(null),[profile,setProfile]=useState<any>(null),[models,setModels]=useState<any[]>([]),[jobs,setJobs]=useState<Job[]>([]),[error,setError]=useState('');
 const refresh=async()=>{try{await json('/health');setConnected(true);const [h,p,m,j]=await Promise.all([json('/hardware'),json('/profile'),json('/models'),json('/jobs')]);setHardware(h);setProfile(p);setModels(m);setJobs(j);setError('')}catch(e){setConnected(false);setError(String(e))}};
 useEffect(()=>{refresh();const timer=setInterval(refresh,1000);return()=>clearInterval(timer)},[]);
 const start=async(gpu:boolean)=>{await json('/jobs/demo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usesGpu:gpu,seconds:8})});refresh()};
 const cancel=async(id:string)=>{await json(`/jobs/${id}/cancel`,{method:'POST'});refresh()};
 return <main><header><div><h1>Whiteboard Video</h1><p>Windows 11 local AI control panel</p></div><span className={connected?'ok':'bad'}>{connected?'Backend online':'Backend offline'}</span></header>
 {error&&<div className="alert">{error}<br/>Chạy: <code>python -m backend.cli serve</code></div>}
 <section className="grid"><article><h2>Hardware</h2><pre>{JSON.stringify(hardware,null,2)}</pre></article><article><h2>Qwen profile</h2><pre>{JSON.stringify(profile,null,2)}</pre></article></section>
 <section><h2>Models</h2><div className="cards">{models.map(m=><div className="model" key={m.id}><b>{m.id}</b><span>{m.installed?'Installed':'Not installed'}</span><small>{m.license}</small></div>)}</div></section>
 <section><div className="row"><h2>Jobs</h2><button onClick={()=>start(false)}>Test CPU job</button><button onClick={()=>start(true)}>Test GPU job</button></div>{jobs.length===0?<p>Chưa có job.</p>:jobs.map(j=><div className="job" key={j.id}><div><b>{j.kind}</b> · {j.status}<small>{j.message}</small></div><progress value={j.progress} max="1"/><button disabled={['completed','failed','cancelled'].includes(j.status)} onClick={()=>cancel(j.id)}>Cancel</button></div>)}</section>
 </main>}
