mod registry;

use registry::Decision;

/// The webview's only way to learn what the harness has decided. Reads
/// `governance/registry.json` from a path resolved at compile time (see
/// `registry::registry_path`), never from the webview, and never mutates
/// anything — this app only reads governance state.
///
/// On any failure — missing file, unreadable file, malformed JSON — this
/// returns `Err` with a message naming what went wrong, rather than `Ok(vec![])`.
/// An empty vector is indistinguishable from "no decisions exist" and would be
/// a false success; see AGENTS.md and the M0.3 brief on this exact hazard.
#[tauri::command]
fn list_decisions() -> Result<Vec<Decision>, String> {
    registry::read_registry(&registry::registry_path()).map_err(|e| e.to_string())
}

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
        .invoke_handler(tauri::generate_handler![list_decisions])
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
