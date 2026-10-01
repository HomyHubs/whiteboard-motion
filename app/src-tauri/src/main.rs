use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_shell::{process::CommandChild, ShellExt};

struct BackendSidecar(Mutex<Option<CommandChild>>);

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendSidecar(Mutex::new(None)))
        .setup(|app| {
            let sidecar = app.shell().sidecar("whiteboard-backend")?;
            let (_events, child) = sidecar.args(["--host", "127.0.0.1", "--port", "8765"]).spawn()?;
            *app.state::<BackendSidecar>().0.lock().unwrap() = Some(child);
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                if let Some(child) = window.state::<BackendSidecar>().0.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("tauri runtime error");
}
