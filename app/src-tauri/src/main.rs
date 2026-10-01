use std::process::{Child,Command,Stdio}; use std::sync::Mutex;
struct Backend(Mutex<Option<Child>>);
fn main(){tauri::Builder::default().manage(Backend(Mutex::new(None))).setup(|app|{
 let child=Command::new("python").args(["-m","backend.cli","serve"]).current_dir("..").stdout(Stdio::null()).stderr(Stdio::null()).spawn().ok();
 *app.state::<Backend>().0.lock().unwrap()=child; Ok(())
}).on_window_event(|window,event|{if let tauri::WindowEvent::Destroyed=event{if let Some(mut child)=window.state::<Backend>().0.lock().unwrap().take(){let _=child.kill();}}}).run(tauri::generate_context!()).expect("tauri runtime error");}
