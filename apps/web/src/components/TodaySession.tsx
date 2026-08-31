"use client";

import { FormEvent, useEffect, useState } from "react";
import { ApiError, assessSession, getGoal, getNextSession, LearnerModel, requestAlternativeExplanation, sendSessionFeedback, Session } from "@/lib/api";
import { RationalePanel } from "@/components/RationalePanel";

type TodaySessionProps = { goalId: string; goalTitle: string };

export function TodaySession({ goalId, goalTitle }: TodaySessionProps) {
  const [session, setSession] = useState<Session>();
  const [beforeModel, setBeforeModel] = useState<LearnerModel>();
  const [afterModel, setAfterModel] = useState<LearnerModel>();
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [pending, setPending] = useState(true);
  const [message, setMessage] = useState("The planner is assembling today’s route…");
  const [error, setError] = useState("");
  const [alternative, setAlternative] = useState("");
  const today = new Date().toISOString().slice(0, 10);

  useEffect(() => {
    Promise.all([getNextSession(goalId, today), getGoal(goalId)]).then(([next, details]) => { setSession(next); setBeforeModel(details.learner_model); setMessage(""); }).catch((caught: unknown) => { setError(caught instanceof ApiError ? caught.message : "Today’s session could not be loaded."); setMessage(""); }).finally(() => setPending(false));
  }, [goalId, today]);

  async function assess(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session?.id) return;
    const retrievalAnswers = session.blocks
      .filter((block) => block.kind === "retrieval")
      .map((block) => ({ item_id: block.concept_id, answer: answers[block.concept_id] ?? "" }))
      .filter((item) => item.answer.length > 0);
    if (retrievalAnswers.length === 0) return;
    setPending(true); setError(""); setMessage("The assessor is checking your evidence…");
    try { const result = await assessSession(session.id, { answers: retrievalAnswers }); setAfterModel(result.learner_model); setMessage("Assessment recorded. The learner model is up to date."); } catch (caught: unknown) { setError(caught instanceof ApiError ? caught.message : "Your assessment could not be saved."); } finally { setPending(false); }
  }

  async function askAlternative() {
    if (!session?.id) return;
    setPending(true); setError(""); setMessage("Finding another explanation…");
    try { const result = await requestAlternativeExplanation(session.id); setAlternative(result.content); setMessage("Alternative explanation ready."); } catch (caught: unknown) { setError(caught instanceof ApiError ? caught.message : "An alternative explanation is unavailable right now."); } finally { setPending(false); }
  }

  if (pending && !session) return <div className="page-grid"><div className="main-rail"><p className="eyebrow">Today · {today}</p><h1>{goalTitle}</h1><p className="form-message" aria-live="polite">{message}</p></div></div>;
  if (!session) return <div className="page-grid"><div className="main-rail"><p className="error-message" role="alert">{error || "No session is available."}</p></div></div>;
  return <div className="page-grid"><div className="main-rail"><div className="session-header"><p className="eyebrow">Today&apos;s route · {session.session_date}</p><h1>Make the next idea stick.</h1><div className="session-meta"><span>{session.total_minutes} minutes</span><span>{session.blocks.length} station{session.blocks.length === 1 ? "" : "s"}</span><span>Session {session.id ?? "pending"}</span></div></div>{session.deadline_status !== "on_track" ? <div className="deadline-banner" role="status"><strong>Deadline signal: {session.deadline_status.replace("_", " ")}</strong><br />The planner has surfaced this route status so you can adjust your pace with intention.</div> : null}<div className="session-blocks">{session.blocks.map((block, index) => <article className="session-block" key={`${block.concept_id}-${index}`}><div className="control-row"><span className="block-index">Station {String(index + 1).padStart(2, "0")}</span><span className="block-kind">{block.kind.replace("_", " ")} · {block.minutes} min</span></div><p className="block-objective">{block.objective}</p>{block.content ? <p className="block-content">{block.content}</p> : null}{block.kind === "retrieval" ? <form className="retrieval-form" onSubmit={assess}><label htmlFor={`retrieval-${index}`}>Write your answer from memory</label><textarea id={`retrieval-${index}`} value={answers[block.concept_id] ?? ""} onChange={(event) => setAnswers((current) => ({ ...current, [block.concept_id]: event.target.value }))} required placeholder="What do you remember?" /><button className="primary-action" type="submit" disabled={pending || !(answers[block.concept_id] ?? "")}>Submit assessment</button></form> : <button className="secondary-action" type="button" onClick={askAlternative} disabled={pending}>Try another explanation</button>}</article>)}</div>{alternative ? <div className="feedback-panel"><div className="section-kicker">Alternate lens</div><p>{alternative}</p></div> : null}{afterModel ? <ModelDelta before={beforeModel} after={afterModel} /> : null}<div className="feedback-panel"><div className="section-kicker">Human signal</div><h2>Was this session appropriate?</h2><FeedbackControls sessionId={session.id ?? "session-demo"} /></div><div aria-live="polite" aria-atomic="true">{message ? <p className="form-message">{message}</p> : null}{error ? <p className="error-message" role="alert">{error}</p> : null}</div></div><aside className="evidence-sidebar"><RationalePanel rationale={session.rationale} deadlineStatus={session.deadline_status} reviewsIncluded={session.reviews_included} deferredConcepts={session.deferred_concepts} /></aside></div>;
}

function ModelDelta({ before, after }: { before?: LearnerModel; after: LearnerModel }) {
  const ids = Object.keys(after.concepts ?? {});
  return <section className="readiness-panel" aria-labelledby="model-delta-heading"><div className="section-kicker">After assessment</div><h2 id="model-delta-heading">Learner model update</h2><p className="muted">Only the change returned by the assessor is shown here.</p>{ids.map((id) => { const next = after.concepts?.[id]; const previous = before?.concepts?.[id]; if (!next) return null; const delta = next.mastery - (previous?.mastery ?? next.mastery); return <p className="source-meta" key={id}>{id}: {delta > 0 ? "+" : ""}{Math.round(delta * 100)} points · now {Math.round(next.mastery * 100)}%</p>; })}</section>;
}

function FeedbackControls({ sessionId }: { sessionId: string }) {
  const [pending, setPending] = useState(false); const [message, setMessage] = useState(""); const [reason, setReason] = useState("");
  async function send(appropriate: boolean) { setPending(true); setMessage(""); try { const response = await sendSessionFeedback(sessionId, { appropriate, reason: reason || null }); setMessage(response.message); } catch (caught: unknown) { setMessage(caught instanceof ApiError ? caught.message : "Feedback could not be saved."); } finally { setPending(false); } }
  return <><div className="button-row"><button className="secondary-action" type="button" onClick={() => send(true)} disabled={pending}>Good fit</button><button className="danger-action" type="button" onClick={() => send(false)} disabled={pending}>Needs adjustment</button></div><label className="field" htmlFor="session-feedback-reason"><span className="label-note">Optional context</span><input id="session-feedback-reason" type="text" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="What should change?" /></label><p className="form-message" aria-live="polite">{message}</p></>;
}
