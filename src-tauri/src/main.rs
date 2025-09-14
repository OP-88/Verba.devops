#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;
use std::process::{Command, Stdio};
use std::path::PathBuf;

#[tauri::command]
fn start_backend() -> Result<String, String> {
    // Get resource directory
    let resource_dir = tauri::utils::platform::resource_dir(&tauri::Env::default())
        .ok_or("Failed to get resource directory")?;
    
    // Path to embedded Python and main.py
    let python_path = resource_dir.join("backend").join("python").join("python");
    let backend_path = resource_dir.join("backend").join("main.py");
    
    // Try different Python executables
    let python_executables = vec![
        python_path,
        PathBuf::from("python3"),
        PathBuf::from("python"),
    ];
    
    for python_exe in python_executables {
        match Command::new(&python_exe)
            .arg(&backend_path)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
        {
            Ok(_) => return Ok(format!("Backend started successfully with {:?}", python_exe)),
            Err(_) => continue,
        }
    }
    
    Err("Failed to start backend with any Python executable".to_string())
}

#[tauri::command]
async fn check_microphone_permission() -> Result<bool, String> {
    // This would check microphone permissions on different platforms
    Ok(true)
}

#[tauri::command] 
async def get_app_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            start_backend,
            check_microphone_permission,
            get_app_version
        ])
        .setup(|app| {
            // Start backend server on app startup
            tauri::async_runtime::spawn(async {
                let _ = start_backend();
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}