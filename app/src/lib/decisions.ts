import { invoke } from '@tauri-apps/api/core'

/**
 * One decision as published by the harness's `governance/registry.json`.
 * Mirrors `registry::Decision` in `src-tauri/src/registry.rs` field for
 * field — this is the TypeScript half of that one IPC contract.
 */
export interface Decision {
  id: string
  title: string
  status: string
  kind: string
  supersededBy: string | null
}

/** The shape the Rust `list_decisions` command actually serialises. */
interface RawDecision {
  id: string
  title: string
  status: string
  kind: string
  superseded_by: string | null
}

function fromRaw(raw: RawDecision): Decision {
  return {
    id: raw.id,
    title: raw.title,
    status: raw.status,
    kind: raw.kind,
    supersededBy: raw.superseded_by,
  }
}

/**
 * Calls the `list_decisions` Tauri command — the webview's only way to read
 * governance state. Never reads a file, opens a socket, or falls back to an
 * empty list on failure: the caller must render whatever error this throws,
 * because an empty list is indistinguishable from "no decisions exist".
 */
export async function fetchDecisions(): Promise<Decision[]> {
  const raw = await invoke<RawDecision[]>('list_decisions')
  return raw.map(fromRaw)
}
