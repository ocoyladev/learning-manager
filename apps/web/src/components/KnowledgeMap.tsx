import type { Concept, LearnerModel } from "@/lib/api";

type KnowledgeMapProps = {
  concepts: Concept[];
  learnerModel: LearnerModel;
};

function stateLabel(state: string): string {
  return state.replace("_", " ");
}

export function KnowledgeMap({ concepts, learnerModel }: KnowledgeMapProps) {
  return (
    <section className="terrain-panel" aria-labelledby="knowledge-map-heading">
      <div className="section-kicker">Learning terrain</div>
      <div className="section-heading-row">
        <div>
          <h2 id="knowledge-map-heading">Knowledge map</h2>
          <p className="muted">The map keeps prerequisite order visible as your confidence changes.</p>
        </div>
        <span className="evidence-tag">LIVE MODEL</span>
      </div>
      <ol className="terrain-rail" aria-label="Concept mastery in prerequisite order">
        {concepts.map((concept, index) => {
          const state = learnerModel.concepts?.[concept.id];
          const mastery = state?.mastery ?? 0;
          const stateName = state?.state ?? "unseen";
          return (
            <li className={`terrain-station station-${stateName}`} key={concept.id}>
              <div className="station-marker" aria-hidden="true">{String(index + 1).padStart(2, "0")}</div>
              <div className="station-copy">
                <div className="station-title-row">
                  <h3>{concept.name}</h3>
                  <span className="state-label">{stateLabel(stateName)}</span>
                </div>
                <div className="mastery-line">
                  <div className="mastery-track" role="progressbar" aria-label={`${concept.name} mastery`} aria-valuemin={0} aria-valuemax={1} aria-valuenow={mastery}>
                    <span style={{ width: `${Math.round(mastery * 100)}%` }} />
                  </div>
                  <span className="mono-value">{Math.round(mastery * 100)}%</span>
                </div>
                <p className="station-detail">
                  {state?.confidence === undefined ? "Not assessed yet" : `${Math.round(state.confidence * 100)}% confidence · ${state.evidence?.[0] ?? "Evidence is still accumulating."}`}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
