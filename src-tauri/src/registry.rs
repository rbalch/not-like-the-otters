//! Read-only access to `governance/registry.json`, the harness's published
//! interface. This module never parses decision markdown or YAML frontmatter
//! itself — that logic belongs to the Python harness (see `AGENTS.md`,
//! "Never let harness logic drift into the Rust crate"). It only deserialises
//! the JSON the harness already generated.

use std::fmt;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

/// One decision as published in `governance/registry.json`.
///
/// Field names match the JSON verbatim so `serde` can derive the mapping
/// without a rename table drifting out of sync with the harness's schema.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Decision {
    pub id: String,
    pub title: String,
    pub status: String,
    pub kind: String,
    pub superseded_by: Option<String>,
}

/// The subset of `registry.json` this module cares about. The file also
/// carries a top-level `controls` array; `serde` ignores fields it isn't
/// told about, so adding to that array elsewhere never breaks this type.
#[derive(Debug, Deserialize)]
struct Registry {
    decisions: Vec<Decision>,
}

/// Everything that can go wrong reading the registry, each variant carrying
/// enough detail to render a real error instead of an empty list.
#[derive(Debug)]
pub enum RegistryError {
    Io { path: PathBuf, source: String },
    Parse { path: PathBuf, source: String },
}

impl fmt::Display for RegistryError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            RegistryError::Io { path, source } => {
                write!(f, "could not read {}: {source}", path.display())
            }
            RegistryError::Parse { path, source } => {
                write!(
                    f,
                    "{} is not valid governance registry JSON: {source}",
                    path.display()
                )
            }
        }
    }
}

impl std::error::Error for RegistryError {}

/// Parse already-read registry content into the decision list. Pure and
/// disk-free, so it is unit-testable without touching the filesystem or
/// depending on the process's cwd.
pub fn parse_registry(content: &str, path: &Path) -> Result<Vec<Decision>, RegistryError> {
    let registry: Registry = serde_json::from_str(content).map_err(|e| RegistryError::Parse {
        path: path.to_path_buf(),
        source: e.to_string(),
    })?;
    Ok(registry.decisions)
}

/// Read and parse the registry at `path`. The only place in this module that
/// touches disk; everything else is parameterised so it can be tested
/// without one.
pub fn read_registry(path: &Path) -> Result<Vec<Decision>, RegistryError> {
    let content = std::fs::read_to_string(path).map_err(|e| RegistryError::Io {
        path: path.to_path_buf(),
        source: e.to_string(),
    })?;
    parse_registry(&content, path)
}

/// Resolve `governance/registry.json` relative to this crate's own source
/// location, not the process's current working directory.
///
/// `CARGO_MANIFEST_DIR` is baked in at compile time as the absolute path of
/// `src-tauri/` on the machine that built the binary. `cwd` differs between
/// `tauri dev`, `cargo test` and a bundled binary launched from a desktop
/// shortcut (see AGENTS.md, "Environment traps", and finding F-1) — resolving
/// from cwd is exactly the trap that bit the hook prefix in M0.1. This app is
/// explicitly single-machine, single-developer, with packaging and
/// distribution out of scope (see AGENTS.md, "Out of scope"), so a path fixed
/// at compile time to the checkout that built the binary is correct here: the
/// binary only ever runs on the machine, and in the checkout, that built it.
pub fn registry_path() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("governance")
        .join("registry.json")
}

#[cfg(test)]
mod tests {
    use super::*;

    const GOOD: &str = r#"{
        "controls": [],
        "decisions": [
            {
                "id": "DEC-0",
                "kind": "negative",
                "status": "accepted",
                "superseded_by": null,
                "title": "No generated file is named AGENTS.md"
            },
            {
                "id": "DEC-1",
                "kind": "positive",
                "status": "superseded",
                "superseded_by": "DEC-2",
                "title": "An old rule"
            }
        ]
    }"#;

    #[test]
    fn parses_decisions_with_superseded_by_surfaced() {
        let decisions = parse_registry(GOOD, Path::new("registry.json")).expect("valid JSON");

        assert_eq!(decisions.len(), 2);
        assert_eq!(decisions[0].id, "DEC-0");
        assert_eq!(decisions[0].status, "accepted");
        assert_eq!(decisions[0].superseded_by, None);
        assert_eq!(decisions[1].id, "DEC-1");
        assert_eq!(decisions[1].status, "superseded");
        assert_eq!(decisions[1].superseded_by.as_deref(), Some("DEC-2"));
    }

    #[test]
    fn malformed_json_is_a_loud_error_not_an_empty_list() {
        let err = parse_registry("{ not json", Path::new("registry.json"))
            .expect_err("malformed JSON must error");

        match err {
            RegistryError::Parse { .. } => {}
            RegistryError::Io { .. } => panic!("expected a Parse error, got Io"),
        }
        assert!(err
            .to_string()
            .contains("not valid governance registry JSON"));
    }

    #[test]
    fn json_missing_the_decisions_field_is_a_loud_error() {
        let err = parse_registry(r#"{"controls": []}"#, Path::new("registry.json"))
            .expect_err("missing `decisions` field must error, not default to empty");

        assert!(matches!(err, RegistryError::Parse { .. }));
    }

    #[test]
    fn missing_file_is_a_loud_error_not_an_empty_list() {
        let missing = std::env::temp_dir().join("not-like-the-otters-registry-missing-test.json");
        // Guarantee it really doesn't exist; ignore if it already didn't.
        let _ = std::fs::remove_file(&missing);

        let err = read_registry(&missing).expect_err("a missing file must error");

        match &err {
            RegistryError::Io { path, .. } => assert_eq!(path, &missing),
            RegistryError::Parse { .. } => panic!("expected an Io error, got Parse"),
        }
        assert!(err.to_string().contains("could not read"));
    }

    #[test]
    fn malformed_file_on_disk_is_a_loud_error() {
        let path = std::env::temp_dir().join("not-like-the-otters-registry-malformed-test.json");
        std::fs::write(&path, "{ this is not json").expect("can write temp file");

        let err = read_registry(&path).expect_err("malformed file content must error");

        let _ = std::fs::remove_file(&path);
        assert!(matches!(err, RegistryError::Parse { .. }));
    }

    /// Sanity check on the real resolution strategy: under `cargo test`,
    /// `CARGO_MANIFEST_DIR` is `src-tauri/`, so this must resolve to the
    /// actual `governance/registry.json` this repo ships and read it
    /// successfully. If this ever fails, the path strategy is wrong, not the
    /// repo state — see the demonstration in the work item report for what
    /// happens when the real file is moved aside.
    #[test]
    fn real_registry_path_resolves_and_reads() {
        let path = registry_path();
        let decisions = read_registry(&path)
            .unwrap_or_else(|e| panic!("expected the real registry to be readable: {e}"));
        assert!(
            decisions.iter().any(|d| d.id == "DEC-0"),
            "expected DEC-0 to be present in the real registry"
        );
    }
}
