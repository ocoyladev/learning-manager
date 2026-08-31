"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, Concept, Dashboard, LearnerModel, startDiagnostic, submitDiagnostic, type AssessmentItem } from "@/lib/api";
import { KnowledgeMap } from "@/components/KnowledgeMap";

type DiagnosticFlowProps = { goalId: string; concepts: Concept[]; initialModel: LearnerModel; dashboard: Dashboard };

export function DiagnosticFlow({ goalId, concepts, initialModel, dashboard }: DiagnosticFlowProps) {
  const router = useRouter();
  const [items, setItems] = useState<AssessmentItem[]>([]);
  const [itemIndex, setItemIndex] = useState(0);
  const [model, setModel] = useState(initialModel);
  const [answer, setAnswer] = useState("");
  const [started, setStarted] = useState(false);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function begin() {
    setPending(true); setError(""); setMessage("The diagnostician is preparing your first question…");
    try { const response = await startDiagnostic(goalId); setItems(response.items); setItemIndex(0); setStarted(response.items.length > 0); setMessage(response.items.length > 0 ? "" : "The diagnostic returned no questions. Your route is ready."); } catch (caught: unknown) { setError(caught instanceof ApiError ? caught.message : "The diagnostic could not start."); setMessage(""); } finally { setPending(false); }
  }

  async function submit() {
    const item = items[itemIndex];
    if (!item || !answer) return;
    setPending(true); setError(""); setMessage("Scoring your answer and updating the knowledge map…");
    try { const response = await submitDiagnostic(goalId, { answers: [{ item_id: item.id, answer }] }); setModel(response.learner_model); setAnswer(""); if (itemIndex + 1 < items.length) { setItemIndex((index) => index + 1); setMessage(""); } else { setStarted(false); setMessage("Diagnostic captured. Your first route is ready."); } } catch (caught: unknown) { setError(caught instanceof ApiError ? caught.message : "The answer could not be saved."); } finally { setPending(false); }
  }

  const item = items[itemIndex];
  if (!started && items.length === 0) return <div className="question-panel"><div className="section-kicker">01 / Signal</div><h2>Start the diagnostic</h2><p className="muted">The question is short by design. It gives the planner its first piece of evidence.</p><button className="primary-action" type="button" onClick={begin} disabled={pending}>{pending ? "Preparing…" : "Begin diagnostic"}</button><Feedback message={message} error={error} /></div>;
  if (started && item) return <div className="question-panel"><div className="diagnostic-progress"><span>Question {String(itemIndex + 1).padStart(2, "0")}</span><span>One of {items.length}</span></div><fieldset className="answer-options"><legend><h2>{item.question}</h2></legend>{(item.options ?? []).map((option) => <label className="answer-option" key={option}><input type="radio" name="diagnostic-answer" value={option} checked={answer === option} onChange={() => setAnswer(option)} /> <span>{option}</span></label>)}</fieldset><div className="button-row"><button className="primary-action" type="button" onClick={submit} disabled={pending || !answer}>{pending ? "Updating map…" : itemIndex + 1 === items.length ? "Save answer" : "Next question"}</button></div><Feedback message={message} error={error} /></div>;
  return <div><KnowledgeMap concepts={concepts} learnerModel={model} /><div className="readiness-panel" style={{ marginTop: "1rem" }}><div className="section-kicker">Route signal</div><h2>Your next step is visible.</h2><p className="muted">{dashboard.why}</p><div className="button-row"><button className="primary-action" type="button" onClick={() => router.push(`/goals/${goalId}/today`)}>Open today&apos;s session</button><button className="secondary-action" type="button" onClick={() => router.push(`/goals/${goalId}`)}>View dashboard</button></div></div><Feedback message={message} error={error} /></div>;
}

function Feedback({ message, error }: { message: string; error: string }) { return <div aria-live="polite" aria-atomic="true">{message ? <p className="form-message">{message}</p> : null}{error ? <p className="error-message" role="alert">{error}</p> : null}</div>; }
