#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use serde_json::Value;

    // A regression test on the shipped config, not a placeholder: it fails if
    // `tauri.conf.json` stops parsing as JSON or its identifier ever drifts from what
    // the rest of the app (bundling, IPC origin checks) assumes it is.
    #[test]
    fn tauri_conf_identifies_this_app() {
        let raw = include_str!("../tauri.conf.json");
        let conf: Value = serde_json::from_str(raw).expect("tauri.conf.json must be valid JSON");

        assert_eq!(conf["identifier"], "dev.balch.not-like-the-otters");
    }
}
