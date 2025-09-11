#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;
use std::process::{Command, Stdio};

#[tauri::command]
fn start_backend() -> Result<String, String> {
    let resource_dir = tauri::api::path::resource_dir(&tauri::api::PackageInfo::new().unwrap(), &tauri::Env::default())
        .ok_or("Failed to get resource directory")?;
    
    let backend_path = resource_dir.join("backend").join("main.py");
    
    match Command::new("python3")
        .arg(backend_path)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(_) => Ok("Backend started successfully".to_string()),
        Err(e) => Err(format!("Failed to start backend: {}", e)),
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![start_backend])
        .setup(|app| {
            // Start backend server
            let _ = start_backend();
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}