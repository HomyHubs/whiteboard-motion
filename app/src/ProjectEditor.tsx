import {useEffect,useState} from 'react';
const API='http://127.0.0.1:8765';
type Project={id:string;name:string;aspectRatio:string;scenes?:string[]};
async function json(path:string,init?:RequestInit){const response=await fetch(API+path,init);const data=await response.json();if(!response.ok)throw new Error(data.error||JSON.stringify(data));return data}
const defaultScene=(id:string)=>({sceneId:id,canvas:{width:1672,height:941,background:'#F5EBD7'},storyBasis:'',sceneDurationMs:10000,assets:[]});
export default function ProjectEditor(){
 const [projects,setProjects]=useState<Project[]>([]),[selected,setSelected]=useState<Project|null>(null),[sceneId,setSceneId]=useState(''),[manifest,setManifest]=useState(''),[message,setMessage]=useState(''),[showPreview,setShowPreview]=useState(false);
 const loadProjects=async()=>setProjects(await json('/projects'));
 useEffect(()=>{loadProjects().catch(e=>setMessage(String(e)))},[]);
 const select=async(id:string)=>{const project=await json(`/projects/${id}`);setSelected(project);setSceneId('');setManifest('');};
 const create=async()=>{const name=prompt('Tên project');if(!name)return;const project=await json('/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});await loadProjects();await select(project.id)};
 const openScene=async(id:string)=>{setSceneId(id);setManifest(JSON.stringify(await json(`/projects/${selected!.id}/scenes/${id}`),null,2))};
 const newScene=()=>{const id=prompt('Scene ID, ví dụ scene-01');if(!id)return;setSceneId(id);setManifest(JSON.stringify(defaultScene(id),null,2))};
 const save=async()=>{if(!selected||!sceneId)return;try{const value=JSON.parse(manifest);await json(`/projects/${selected.id}/scenes/${sceneId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});setMessage('Đã lưu scene atomically.');await select(selected.id);await openScene(sceneId)}catch(e){setMessage(String(e))}};
 return <section><div className="row"><div><h2>Project & Scene Editor</h2><small>Project lưu trong app-data; JSON scene dùng cho RGBA composition và annotation.</small></div><button onClick={create}>New project</button></div>
 <div className="editor-grid"><aside><h3>Projects</h3>{projects.map(p=><button className={selected?.id===p.id?'list active':'list'} key={p.id} onClick={()=>select(p.id)}>{p.name}</button>)}{selected&&<><h3>Scenes</h3>{selected.scenes?.map(id=><button className={sceneId===id?'list active':'list'} key={id} onClick={()=>openScene(id)}>{id}</button>)}<button className="list add" onClick={newScene}>+ New scene</button></>}</aside>
 <div className="scene-editor">{selected?<><div className="row"><b>{selected.name}{sceneId?` / ${sceneId}`:''}</b><div><button disabled={!sceneId} onClick={save}>Save scene</button> <button onClick={()=>setShowPreview(!showPreview)}>{showPreview?'Close preview':'Open annotation preview'}</button></div></div>{message&&<p className="editor-message">{message}</p>}{sceneId?<textarea value={manifest} onChange={e=>setManifest(e.target.value)} spellCheck={false}/>:<p>Chọn hoặc tạo scene.</p>}</>:<p>Chọn project để bắt đầu.</p>}</div></div>
 {showPreview&&<div className="preview-wrap"><iframe title="Whiteboard annotation preview" src={`${API}/preview`} allow="clipboard-read; clipboard-write"/></div>}</section>}
