import type { Decision } from '../lib/decisions'

/**
 * Maps a decision's status to a Classical tag variant class.
 *
 * `Decision.status` is typed `string`, not a union: it comes from
 * `governance/registry.json` over IPC, and the harness can introduce a new
 * status (e.g. `proposed`, `rejected`) without this component changing.
 * Any status not explicitly known falls back to `tag-outline` — the status
 * text still renders verbatim. Failing closed here means showing the
 * unknown value, never hiding it: a decision whose status the UI does not
 * recognise is exactly the one a human needs to see.
 */
function tagClassFor(status: string): string {
  switch (status) {
    case 'accepted':
      return 'tag-accent'
    case 'superseded':
      return 'tag-neutral'
    default:
      return 'tag-outline'
  }
}

/** Presentational only: renders Classical's table for a list of decisions.
 * Does not fetch, invoke a Tauri command, or otherwise know how the
 * decisions it is given were loaded. */
export default function DecisionTable({
  decisions,
}: {
  decisions: Decision[]
}) {
  return (
    <table className="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Status</th>
          <th>Superseded by</th>
        </tr>
      </thead>
      <tbody>
        {decisions.map((decision) => (
          <tr key={decision.id}>
            <td>{decision.id}</td>
            <td>{decision.title}</td>
            <td>
              <span className={`tag ${tagClassFor(decision.status)}`}>
                {decision.status}
              </span>
            </td>
            <td className="text-muted">
              {decision.supersededBy
                ? `superseded by ${decision.supersededBy}`
                : ''}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
