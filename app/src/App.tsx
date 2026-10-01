import {useEffect,useState} from 'react';
import ProjectEditor from './ProjectEditor';
const API='http://127.0.0.1:8765';
type Job={id:string;kind:string;status:string;progress:number;message:string;uses_gpu:boolean};
type Model={id:string;revision:string;download_bytes?:number;license:string;license_url?:string;requires_acceptance?:boolean;license_accepted:boolean;installed:boolean;purpose:string};
async function json(path:string,init?:RequestInit){const r=await fetch(API+path,init);const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.error||JSON.stringify(data));return data}
const bytes=(value?:number)=>value?`${(value/1024/1024/1024).toFixed(2)} GB`:'Unknown size';
export default function App(){
 const [connected,setConnected]=useState(false),[hardware,setHardware]=useState<any>(null),[profile,setProfile]=useState<any>(null),[models,setModels]=useState<Model[]>([]),[jobs,setJobs]=useState<Job[]>([]),[error,setError]=useState(''),[notice,setNotice]=useState(''),[media,setMedia]=useState<any>(null),[update,setUpdate]=useState<any>(null),[checking,setChecking]=useState(false);
 const refresh=async()=>{try{await json('/health');setConnected(true);const [h,p,m,j]=await Promise.all([json('/hardware'),json('/profile'),json('/models'),json('/jobs')]);setHardware(h);setProfile(p);setModels(m);setJobs(j);setError('')}catch(e){setConnected(false);setError(String(e))}};
 useEffect(()=>{refresh();const timer=setInterval(refresh,1000);return()=>clearInterval(timer)},[]);
 useEffect(()=>{if(connected&&!media)json('/media').then(setMedia).catch(()=>{})},[connected]);
 const checkUpdate=async()=>{setChecking(true);try{setUpdate(await json('/updates'))}catch(e){setUpdate({error:String(e)})}finally{setChecking(false)}};
 const action=async(fn:()=>Promise<any>)=>{try{const result=await fn();setNotice(JSON.stringify(result));setError('');refresh()}catch(e){setError(String(e))}};
 const accept=(m:Model)=>{if(confirm(`Bạn đã đọc và chấp nhận license của ${m.id}?\n${m.license}`))action(()=>json(`/models/${m.id}/accept`,{method:'POST'}))};
 const download=(m:Model)=>{if(confirm(`Tải ${m.id} (${bytes(m.download_bytes)})?`))action(()=>json(`/models/${m.id}/download`,{method:'POST'}))};
 const verify=(m:Model)=>action(()=>json(`/models/${m.id}/verify`,{method:'POST'}));
 const remove=(m:Model)=>{if(confirm(`Xóa model ${m.id} khỏi máy?`))action(()=>json(`/models/${m.id}`,{method:'DELETE'}))};
 const start=async(gpu:boolean)=>{await json('/jobs/demo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usesGpu:gpu,seconds:8})});refresh()};
 const cancel=async(id:string)=>{await json(`/jobs/${id}/cancel`,{method:'POST'});refresh()};
 const downloading=(id:string)=>jobs.some(j=>j.kind===`model-download:${id}`&&!['completed','failed','cancelled'].includes(j.status));
 return <main><header><div><h1>Whiteboard Video</h1><p>Windows 11 local AI control panel</p></div><span className={connected?'ok':'bad'}>{connected?'Backend online':'Backend offline'}</span></header>
 {error&&<div className="alert">{error}<br/>Chạy: <code>python -m backend.cli serve</code></div>}{notice&&<div className="notice">{notice}</div>}
 <section className="grid"><article><h2>Hardware</h2><pre>{JSON.stringify(hardware,null,2)}</pre></article><article><h2>Qwen profile</h2><pre>{JSON.stringify(profile,null,2)}</pre></article><article><h2>Video encoder</h2>{media?.ffmpeg?<><p><b>{media.encoder?.name||media.encoder?.error}</b> {media.encoder?.hardware?'(NVIDIA NVENC)':'(CPU libx264)'}</p><small>FFmpeg: {media.source} · {media.license}</small></>:<p>{media?'Không tìm thấy FFmpeg':'…'}</p>}</article><article><h2>Cập nhật</h2><button disabled={checking||!connected} onClick={checkUpdate}>{checking?'Đang kiểm tra…':'Kiểm tra cập nhật'}</button>{update&&(update.error?<p>{update.error}</p>:update.updateAvailable?<p>Có bản mới <b>{update.latest}</b> (đang dùng {update.current}). Tải tại: <code>{update.releaseUrl}</code></p>:<p>Đang dùng bản mới nhất ({update.current}).</p>)}<small>App không tự tải hay cài bản cập nhật.</small></article></section>
 <ProjectEditor/>
 <section><h2>Model Manager</h2><div className="cards">{models.map(m=><div className="model" key={m.id}><div className="row"><b>{m.id}</b><span className={m.installed?'tag installed':'tag'}>{m.installed?'Installed':'Not installed'}</span></div><small>{m.purpose} · {bytes(m.download_bytes)}</small><small>Revision: <code>{m.revision.slice(0,12)}</code></small><small>{m.license_url?<a href={m.license_url} target="_blank">{m.license}</a>:m.license}</small><div className="buttons">{m.requires_acceptance&&!m.license_accepted&&<button onClick={()=>accept(m)}>Accept license</button>}<button disabled={m.installed||downloading(m.id)||(!!m.requires_acceptance&&!m.license_accepted)} onClick={()=>download(m)}>{downloading(m.id)?'Downloading…':'Download'}</button><button disabled={!m.installed} onClick={()=>verify(m)}>Verify</button><button className="danger" disabled={!m.installed} onClick={()=>remove(m)}>Delete</button></div></div>)}</div></section>
 <section><div className="row"><h2>Jobs</h2><div><button onClick={()=>start(false)}>Test CPU job</button> <button onClick={()=>start(true)}>Test GPU job</button></div></div>{jobs.length===0?<p>Chưa có job.</p>:jobs.map(j=><div className="job" key={j.id}><div><b>{j.kind}</b> · {j.status}<small>{j.message}</small></div><progress value={j.progress} max="1"/><button disabled={['completed','failed','cancelled'].includes(j.status)} onClick={()=>cancel(j.id)}>Cancel</button></div>)}</section>
 </main>}
