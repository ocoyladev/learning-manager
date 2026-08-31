"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, assessSession, AssessmentResponse, getGoal, getNextSession, LearnerConceptState, LearnerModel, requestAlternativeExplanation, sendSessionFeedback, Session } from "@/lib/api";
import { RationalePanel } from "@/components/RationalePanel";

type TodaySessionProps = { goalId: string; goalTitle: string };
type DisplayField = "mastery" | "confidence" | "state" | "next_review";
const displayFields: DisplayField[] = ["mastery", "confidence", "state", "next_review"];

export function TodaySession({ goalId, goalTitle }: TodaySessionProps) {
  const [session, setSession] = useState<Session>();
  const [beforeModel, setBeforeModel] = useState<LearnerModel>();
  const [afterModel, setAfterModel] = useState<LearnerModel>();
  const [results, setResults] = useState<AssessmentResponse["results"]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [pending, setPending] = useState(true);
  const [message, setMessage] = useState("The planner is assembling today’s route…");
  const [error, setError] = useState("");
  const [alternative, setAlternative] = useState("");
  const today = new Date().toISOString().slice(0, 10);

  useEffect(() => {
    Promise.all([getNextSession(goalId, today), getGoal(goalId)])
      .then(([next, details]) => { setSession(next); setBeforeModel(details.learner_model); setMessage(""); })
      .catch((caught: unknown) => { setError(caught instanceof ApiError ? caught.message : "Today’s session could not be loaded."); setMessage(""); })
      .finally(() => setPending(false));
  }, [goalId, today]);

  async function assess(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const currentSession = session;
    const sessionId = getSessionId(currentSession);
    if (!currentSession || !sessionId) return;
    const retrievalAnswers = currentSession.blocks.filter((block) => block.kind === "retrieval").map((block) => ({ item_id: block.concept_id, answer: answers[block.concept_id] ?? "" })).filter((item) => item.answer.length > 0);
    if (retrievalAnswers.length === 0) return;
    setPending(true); setError(""); setMessage("The assessor is checking your evidence…");
    try { const assessment = await assessSession(sessionId, { answers: retrievalAnswers }); const details = await getGoal(goalId); setResults(assessment.results); setAfterModel(details.learner_model); setMessage("Assessment recorded. The learner model is up to date."); }
    catch (caught: unknown) { setError(caught instanceof ApiError ? caught.message : "Your assessment could not be saved."); }
    finally { setPending(false); }
  }

  async function askAlternative() {
    const sessionId = getSessionId(session);
    if (!sessionId) return;
    setPending(true); setError(""); setMessage("Finding another explanation…");
    try { const result = await requestAlternativeExplanation(sessionId); setAlternative(result.content); setMessage("Alternative explanation ready."); }
    catch (caught: unknown) { setError(caught instanceof ApiError ? caught.message : "An alternative explanation is unavailable right now."); }
    finally { setPending(false); }
  }

  if (pending && !session) return <div className="page-grid"><div className="main-rail"><p className="eyebrow">Today · {today}</p><h1>{goalTitle}</h1><p className="form-message" aria-live="polite">{message}</p></div></div>;
  if (!session) return <div className="page-grid"><div className="main-rail"><p className="error-message" role="alert">{error || "No session is available."}</p></div></div>;

  const sessionId = getSessionId(session);
  const hasSessionId = sessionId !== undefined;
  return <div className="page-grid"><div className="main-rail"><div className="session-header"><p className="eyebrow">Today&apos;s route · {session.session_date}</p><h1>Make the next idea stick.</h1><div className="session-meta"><span>{session.total_minutes} minutes</span><span>{session.blocks.length} station{session.blocks.length === 1 ? "" : "s"}</span><span>{hasSessionId ? `Session ${session.id}` : "Session awaiting assignment"}</span></div><Link className="secondary-action" href={`/goals/${goalId}`}>Back to dashboard</Link></div>{session.deadline_status !== "on_track" ? <div className="deadline-banner" role="status"><strong>Deadline signal: {session.deadline_status.replace("_", " ")}</strong><br />The planner has surfaced this route status so you can adjust your pace with intention.</div> : null}{!hasSessionId ? <p className="error-message" role="alert">This session is not ready for feedback or follow-up requests yet.</p> : null}<div className="session-blocks">{session.blocks.map((block, index) => <article className="session-block" key={`${block.concept_id}-${index}`}><div className="control-row"><span className="block-index">Station {String(index + 1).padStart(2, "0")}</span><span className="block-kind">{block.kind.replace("_", " ")} · {block.minutes} min</span></div><p className="block-objective">{block.objective}</p>{block.content ? <p className="block-content">{block.content}</p> : null}{block.kind === "retrieval" ? <form className="retrieval-form" onSubmit={assess}><label htmlFor={`retrieval-${index}`}>Write your answer from memory</label><textarea id={`retrieval-${index}`} value={answers[block.concept_id] ?? ""} onChange={(event) => setAnswers((current) => ({ ...current, [block.concept_id]: event.target.value }))} required placeholder="What do you remember?" /><button className="primary-action" type="submit" disabled={pending || !hasSessionId || !(answers[block.concept_id] ?? "")}>Submit assessment</button></form> : <button className="secondary-action" type="button" onClick={askAlternative} disabled={pending || !hasSessionId}>Try another explanation</button>}</article>)}</div>{alternative ? <div className="feedback-panel"><div className="section-kicker">Alternate lens</div><p>{alternative}</p></div> : null}{results.length > 0 ? <AssessmentEvidence results={results} /> : null}{afterModel ? <ModelDelta before={beforeModel} after={afterModel} /> : null}<div className="feedback-panel"><div className="section-kicker">Human signal</div><h2>Was this session appropriate?</h2><FeedbackControls sessionId={sessionId} /></div><div aria-live="polite" aria-atomic="true">{message ? <p className="form-message">{message}</p> : null}{error ? <p className="error-message" role="alert">{error}</p> : null}</div></div><aside className="evidence-sidebar"><RationalePanel rationale={session.rationale} deadlineStatus={session.deadline_status} reviewsIncluded={session.reviews_included} deferredConcepts={session.deferred_concepts} /></aside></div>;
}

function AssessmentEvidence({ results }: { results: AssessmentResponse["results"] }) {
  return <section className="readiness-panel" aria-labelledby="assessment-evidence-heading"><div className="section-kicker">Assessment evidence</div><h2 id="assessment-evidence-heading">What the assessor recorded</h2>{results.map((result) => <div key={result.concept_id}><p className="source-meta">{result.concept_id} · {result.correct}/{result.total} correct · score {result.score}</p>{result.evidence?.map((evidence) => <p key={evidence}>{evidence}</p>)}{result.misconceptions?.map((misconception) => <p className="source-meta" key={misconception}>Misconception: {misconception}</p>)}</div>)}</section>;
}

function ModelDelta({ before, after }: { before?: LearnerModel; after: LearnerModel }) {
  const ids = Object.keys(after.concepts ?? {});
  return <section className="readiness-panel" aria-labelledby="model-delta-heading"><div className="section-kicker">After assessment</div><h2 id="model-delta-heading">Learner model update</h2><p className="muted">Only API-provided learner-model fields are compared here.</p>{ids.map((id) => <ConceptChange key={id} before={before?.concepts?.[id]} after={after.concepts?.[id]} />)}</section>;
}

function ConceptChange({ before, after }: { before?: LearnerConceptState; after?: LearnerConceptState }) {
  if (!after) return null;
  const changes = displayFields.filter((field) => before?.[field] !== after[field]);
  if (changes.length === 0) return <p className="source-meta">{after.concept_id}: no learner-model change returned by the API.</p>;
  return <p className="source-meta">{after.concept_id}: {changes.map((field) => `${field.replace("_", " ")} ${String(before?.[field] ?? "not recorded")} → ${String(after[field] ?? "not scheduled")}`).join(" · ")}</p>;
}

function getSessionId(session: Session | undefined): string | undefined {
  return typeof session?.id === "string" && session.id.length > 0 ? session.id : undefined;
}

function FeedbackControls({ sessionId }: { sessionId: string | null | undefined }) {
  const [pending, setPending] = useState(false); const [message, setMessage] = useState(""); const [error, setError] = useState(""); const [reason, setReason] = useState("");
  const canSend = sessionId !== null && sessionId !== undefined;
  async function send(appropriate: boolean) { if (!canSend) return; setPending(true); setMessage(""); setError(""); try { const response = await sendSessionFeedback(sessionId, { appropriate, reason: reason || null }); setMessage(response.message); } catch (caught: unknown) { setError(caught instanceof ApiError ? caught.message : "Feedback could not be saved."); } finally { setPending(false); } }
  return <><div className="button-row"><button className="secondary-action" type="button" onClick={() => send(true)} disabled={pending || !canSend}>Good fit</button><button className="danger-action" type="button" onClick={() => send(false)} disabled={pending || !canSend}>Needs adjustment</button></div><label className="field" htmlFor="session-feedback-reason"><span className="label-note">Optional context</span><input id="session-feedback-reason" type="text" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="What should change?" disabled={!canSend} /></label><div aria-live="polite" aria-atomic="true">{message ? <p className="form-message">{message}</p> : null}</div>{error ? <p className="error-message" role="alert">{error}</p> : null}</>;
}
