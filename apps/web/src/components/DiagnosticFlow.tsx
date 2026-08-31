"use client";

import { useState } from "react";
import Link from "next/link";
import { ApiError, AnswersRequest, Concept, Dashboard, getDashboard, LearnerModel, startDiagnostic, submitDiagnostic, type AssessmentItem } from "@/lib/api";
import { KnowledgeMap } from "@/components/KnowledgeMap";

type DiagnosticFlowProps = { goalId: string; concepts: Concept[]; initialModel: LearnerModel; dashboard: Dashboard };

export function DiagnosticFlow({ goalId, concepts, initialModel, dashboard }: DiagnosticFlowProps) {
  const [items, setItems] = useState<AssessmentItem[]>([]);
  const [itemIndex, setItemIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswersRequest["answers"]>([]);
  const [model, setModel] = useState(initialModel);
  const [readiness, setReadiness] = useState<Dashboard | undefined>(dashboard);
  const [readinessError, setReadinessError] = useState("");
  const [answer, setAnswer] = useState("");
  const [started, setStarted] = useState(false);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function begin() {
    setPending(true); setError(""); setMessage("The diagnostician is preparing your first question…");
    try { const response = await startDiagnostic(goalId); setItems(response.items); setItemIndex(0); setAnswers([]); setStarted(response.items.length > 0); setMessage(response.items.length > 0 ? "" : "The diagnostic returned no questions. Your route is ready."); } catch (caught: unknown) { setError(caught instanceof ApiError ? caught.message : "The diagnostic could not start."); setMessage(""); } finally { setPending(false); }
  }

  async function submit() {
    const item = items[itemIndex];
    if (!item || !answer) return;
    const nextAnswers = [...answers, { item_id: item.id, answer }];
    if (itemIndex + 1 < items.length) { setAnswers(nextAnswers); setAnswer(""); setItemIndex((index) => index + 1); return; }
    setPending(true); setError(""); setMessage("Scoring your answers and updating the knowledge map…");
    try {
      let acceptedModel: LearnerModel;
      try { const response = await submitDiagnostic(goalId, { answers: nextAnswers }); acceptedModel = response.learner_model; } catch (caught: unknown) { setError(caught instanceof ApiError ? caught.message : "The answers could not be saved."); return; }
      setModel(acceptedModel); setAnswers(nextAnswers); setAnswer(""); setStarted(false); setReadiness(undefined); setReadinessError("");
      await refreshReadiness("Diagnostic captured. Your first route is ready.");
    } finally { setPending(false); }
  }

  async function refreshReadiness(successMessage: string) {
    try { const refreshedDashboard = await getDashboard(goalId); setReadiness(refreshedDashboard); setReadinessError(""); setMessage(successMessage); } catch { setReadinessError("Diagnostic saved, but readiness could not be refreshed."); setMessage(""); }
  }

  async function retryReadiness() {
    setPending(true); setMessage("Refreshing route readiness…");
    try { await refreshReadiness("Readiness refreshed."); } finally { setPending(false); }
  }

  const item = items[itemIndex];
  if (!started && items.length === 0) return <div className="question-panel"><div className="section-kicker">01 / Signal</div><h2>Start the diagnostic</h2><p className="muted">The question is short by design. It gives the planner its first piece of evidence.</p><button className="primary-action" type="button" onClick={begin} disabled={pending}>{pending ? "Preparing…" : "Begin diagnostic"}</button><Feedback message={message} error={error} /></div>;
  if (started && item) return <div className="question-panel"><div className="diagnostic-progress"><span>Question {String(itemIndex + 1).padStart(2, "0")}</span><span>One of {items.length}</span></div><fieldset className="answer-options"><legend><h2>{item.question}</h2></legend>{(item.options ?? []).map((option) => <label className="answer-option" key={option}><input type="radio" name="diagnostic-answer" value={option} checked={answer === option} onChange={() => setAnswer(option)} /> <span>{option}</span></label>)}</fieldset><div className="button-row"><button className="primary-action" type="button" onClick={submit} disabled={pending || !answer}>{pending ? "Updating map…" : itemIndex + 1 === items.length ? "Save answer" : "Next question"}</button></div><Feedback message={message} error={error} /></div>;
  return <div><KnowledgeMap concepts={concepts} learnerModel={model} /><div className="readiness-panel" style={{ marginTop: "1rem" }}><div className="section-kicker">Route signal</div><h2>Your next step is visible.</h2>{readiness ? <><p className="muted">{readiness.why}</p><div className="readiness-grid"><div><span className="readiness-value">{readiness.estimated_sessions}</span><span className="readiness-label">Sessions</span></div><div><span className="readiness-value">{readiness.projected_completion}</span><span className="readiness-label">Projected</span></div><div><span className="readiness-value">{readiness.deadline_status}</span><span className="readiness-label">Deadline signal</span></div></div></> : <div><p className={readinessError ? "error-message" : "form-message"} role={readinessError ? "alert" : undefined}>{readinessError || "Refreshing route readiness…"}</p><button className="secondary-action" type="button" onClick={retryReadiness} disabled={pending}>{pending ? "Refreshing…" : "Retry readiness"}</button></div>}<div className="button-row"><Link className="primary-action" href={`/goals/${goalId}/today`}>Open today&apos;s session</Link><Link className="secondary-action" href={`/goals/${goalId}`}>View dashboard</Link></div></div><Feedback message={message} error={error} /></div>;
}

function Feedback({ message, error }: { message: string; error: string }) { return <div aria-live="polite" aria-atomic="true">{message ? <p className="form-message">{message}</p> : null}{error ? <p className="error-message" role="alert">{error}</p> : null}</div>; }
