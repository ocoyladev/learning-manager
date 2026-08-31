"use client";

import { FormEvent, useState } from "react";
import { ApiError, createGoal } from "@/lib/api";

const formats = ["Hands-on examples", "Short explanations", "Recall questions"];

export function GoalForm() {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [validationMessages, setValidationMessages] = useState<Record<string, string>>({});

  function showFieldError(event: FormEvent<HTMLInputElement | HTMLTextAreaElement>) {
    const field = event.currentTarget;
    setValidationMessages((current) => ({ ...current, [field.name]: field.validationMessage }));
  }

  function clearFieldError(fieldName: string) {
    setValidationMessages((current) => ({ ...current, [fieldName]: "" }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    const preferredFormats = formats.filter((format) => data.getAll("formats").includes(format));
    setPending(true);
    setMessage("Breaking your goal into concepts…");
    try {
      const result = await createGoal({
        title: String(data.get("title")),
        purpose: String(data.get("purpose")),
        deadline: String(data.get("deadline")),
        daily_minutes: Number(data.get("daily_minutes")),
        preferred_formats: preferredFormats,
      });
      window.location.assign(`/goals/${result.goal.id}/diagnostic`);
    } catch (caught: unknown) {
      setError(caught instanceof ApiError ? caught.message : "The goal could not be created. Check your connection and try again.");
      setPending(false);
      setMessage("");
    }
  }

  return (
    <form className="form-panel" onSubmit={submit} noValidate={false}>
      <div className="section-kicker">Start with a clear bearing</div>
      <h2>What are you learning next?</h2>
      <p className="muted">The navigator will turn your answer into a prerequisite route and a first diagnostic.</p>
      <div className="field-grid">
        <div className="field field-wide">
          <label htmlFor="goal-title">Learning goal <span className="label-note">Be concrete</span></label>
          <input id="goal-title" name="title" type="text" placeholder="Ship a reliable Docker service" required minLength={3} aria-describedby={validationMessages.title ? "goal-title-error" : undefined} onInvalid={showFieldError} onInput={() => clearFieldError("title")} />
          {validationMessages.title ? <p className="error-message" id="goal-title-error" role="alert">{validationMessages.title}</p> : null}
        </div>
        <div className="field field-wide">
          <label htmlFor="goal-purpose">Why does this matter?</label>
          <textarea id="goal-purpose" name="purpose" placeholder="I want to deploy my backend with confidence." required minLength={5} aria-describedby={validationMessages.purpose ? "goal-purpose-error" : undefined} onInvalid={showFieldError} onInput={() => clearFieldError("purpose")} />
          {validationMessages.purpose ? <p className="error-message" id="goal-purpose-error" role="alert">{validationMessages.purpose}</p> : null}
        </div>
        <div className="field">
          <label htmlFor="goal-deadline">Target date</label>
          <input id="goal-deadline" name="deadline" type="date" required min={new Date(Date.now() + 86400000).toISOString().slice(0, 10)} aria-describedby={validationMessages.deadline ? "goal-deadline-error" : undefined} onInvalid={showFieldError} onInput={() => clearFieldError("deadline")} />
          {validationMessages.deadline ? <p className="error-message" id="goal-deadline-error" role="alert">{validationMessages.deadline}</p> : null}
          <span className="label-note">A future date keeps the route honest.</span>
        </div>
        <div className="field">
          <label htmlFor="daily-minutes">Minutes per day</label>
          <input id="daily-minutes" name="daily_minutes" type="number" min={5} max={240} defaultValue={30} required aria-describedby={validationMessages.daily_minutes ? "daily-minutes-error" : undefined} onInvalid={showFieldError} onInput={() => clearFieldError("daily_minutes")} />
          {validationMessages.daily_minutes ? <p className="error-message" id="daily-minutes-error" role="alert">{validationMessages.daily_minutes}</p> : null}
          <span className="label-note">5–240 minutes</span>
        </div>
      </div>
      <fieldset className="format-options">
        <legend>Preferred formats <span className="label-note">Choose any</span></legend>
        {formats.map((format) => <label className="format-option" key={format}><input type="checkbox" name="formats" value={format} />{format}</label>)}
      </fieldset>
      <div className="button-row">
        <button className="primary-action" type="submit" disabled={pending}>{pending ? "Mapping your route…" : "Create learning route"}</button>
      </div>
      <div aria-live="polite" aria-atomic="true">
        {message ? <p className="form-message">{message}</p> : null}
        {error ? <p className="error-message" role="alert">{error}</p> : null}
      </div>
    </form>
  );
}
