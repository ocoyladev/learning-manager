type RationalePanelProps = {
  rationale: string;
  deadlineStatus?: string;
  reviewsIncluded?: string[];
  deferredConcepts?: string[];
};

export function RationalePanel({ rationale, deadlineStatus, reviewsIncluded = [], deferredConcepts = [] }: RationalePanelProps) {
  return (
    <section className="rationale-panel" aria-labelledby="rationale-heading">
      <div className="section-kicker">Decision record</div>
      <h2 id="rationale-heading">Why this session?</h2>
      <p className="rationale-copy">{rationale}</p>
      <dl className="decision-facts">
        {deadlineStatus ? <div><dt>Deadline signal</dt><dd>{deadlineStatus.replace("_", " ")}</dd></div> : null}
        {reviewsIncluded.length > 0 ? <div><dt>Reviews included</dt><dd>{reviewsIncluded.join(", ")}</dd></div> : null}
        {deferredConcepts.length > 0 ? <div><dt>Deferred</dt><dd>{deferredConcepts.join(", ")}</dd></div> : null}
      </dl>
    </section>
  );
}
