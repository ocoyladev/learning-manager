import type { Source } from "@/lib/api";

export function SourcePanel({ sources }: { sources: Source[] }) {
  return <section className="source-panel" aria-labelledby="sources-heading"><div className="section-kicker">Evidence ledger</div><h2 id="sources-heading">Sources behind the route</h2><ul className="source-list">{sources.map((source) => <li key={source.id}><a href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a><p className="source-meta">{source.authority} · {source.version ?? "Version not stated"}<br />Retrieved {source.retrieved_at}</p></li>)}</ul></section>;
}
