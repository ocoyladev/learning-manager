import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { TodaySession } from "@/components/TodaySession";
import type { AssessmentResponse } from "@/lib/api";

const apiMocks = vi.hoisted(() => ({ assessSession: vi.fn(), getGoal: vi.fn(), getNextSession: vi.fn() }));

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, assessSession: apiMocks.assessSession, getGoal: apiMocks.getGoal, getNextSession: apiMocks.getNextSession };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("TodaySession", () => {
  it("refetches the learner model only after assessment succeeds and renders API evidence", async () => {
    const beforeModel = { goal_id: "goal-1", concepts: { containers: { concept_id: "containers", mastery: 0.4, confidence: 0.6, state: "developing" as const, next_review: "2026-09-02" } } };
    const afterModel = { goal_id: "goal-1", concepts: { containers: { concept_id: "containers", mastery: 0.9, confidence: 0.8, state: "mastered" as const, next_review: "2026-09-09" } } };
    const goal = { id: "goal-1", title: "Containers", purpose: "Build reliable services", deadline: "2026-09-20", daily_minutes: 30, preferred_formats: ["examples"] };
    const concepts = [{ id: "containers", name: "Containers", importance: 1, estimated_minutes: 15, prerequisites: [] }];
    apiMocks.getGoal.mockResolvedValueOnce({ goal, concepts, learner_model: beforeModel }).mockResolvedValueOnce({ goal, concepts, learner_model: afterModel });
    apiMocks.getNextSession.mockResolvedValueOnce({ id: "session-1", blocks: [{ concept_id: "containers", kind: "retrieval", minutes: 10, objective: "Recall containers" }], deadline_status: "on_track", rationale: "Review the weak point.", session_date: "2026-09-01", total_minutes: 10 });
    let resolveAssessment: (value: AssessmentResponse) => void = () => undefined;
    const assessment = new Promise<AssessmentResponse>((resolve) => { resolveAssessment = resolve; });
    apiMocks.assessSession.mockReturnValueOnce(assessment);

    render(<TodaySession goalId="goal-1" goalTitle="Containers" />);
    await screen.findByText("Recall containers");
    fireEvent.change(screen.getByLabelText("Write your answer from memory"), { target: { value: "A process and its dependencies" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit assessment" }));

    await waitFor(() => expect(apiMocks.assessSession).toHaveBeenCalledTimes(1));
    expect(apiMocks.getGoal).toHaveBeenCalledTimes(1);

    const response: AssessmentResponse = { results: [{ concept_id: "containers", score: 1, correct: 1, total: 1, evidence: ["The answer identifies process isolation."], misconceptions: [] }], learner_model: afterModel };
    resolveAssessment(response);
    await screen.findByText("The answer identifies process isolation.");
    await waitFor(() => expect(apiMocks.getGoal).toHaveBeenCalledTimes(2));
    expect(screen.getByText(/mastery 0.4 → 0.9/)).toBeInTheDocument();
    expect(screen.getByText(/confidence 0.6 → 0.8/)).toBeInTheDocument();
    expect(screen.getByText(/state developing → mastered/)).toBeInTheDocument();
    expect(screen.getByText(/next review 2026-09-02 → 2026-09-09/)).toBeInTheDocument();
  });

  it("submits one complete ordered assessment for multiple retrieval blocks", async () => {
    const learnerModel = { goal_id: "goal-1", concepts: {} };
    const goal = { id: "goal-1", title: "Containers", purpose: "Build reliable services", deadline: "2026-09-20", daily_minutes: 30, preferred_formats: ["examples"] };
    const concepts = [{ id: "containers", name: "Containers", importance: 1, estimated_minutes: 15, prerequisites: [] }];
    apiMocks.getGoal.mockResolvedValueOnce({ goal, concepts, learner_model: learnerModel });
    apiMocks.getNextSession.mockResolvedValueOnce({ id: "session-1", blocks: [
      { concept_id: "runtime", kind: "retrieval", minutes: 10, objective: "Recall runtime isolation" },
      { concept_id: "networking", kind: "retrieval", minutes: 10, objective: "Recall container networking" },
    ], deadline_status: "on_track", rationale: "Review both weak points.", session_date: "2026-09-01", total_minutes: 20 });
    apiMocks.assessSession.mockResolvedValueOnce({ results: [{ concept_id: "runtime", score: 1, correct: 1, total: 1, evidence: ["Runtime evidence"], misconceptions: [] }, { concept_id: "networking", score: 1, correct: 1, total: 1, evidence: ["Networking evidence"], misconceptions: [] }], learner_model: learnerModel });

    render(<TodaySession goalId="goal-1" goalTitle="Containers" />);
    await screen.findByText("Recall runtime isolation");
    const fields = screen.getAllByRole("textbox");
    const submit = screen.getByRole("button", { name: "Submit assessment" });
    expect(submit).toBeDisabled();
    fireEvent.change(fields[0], { target: { value: "A process" } });
    expect(submit).toBeDisabled();
    fireEvent.change(fields[1], { target: { value: "A virtual network" } });
    expect(submit).not.toBeDisabled();
    fireEvent.click(submit);

    await waitFor(() => expect(apiMocks.assessSession).toHaveBeenCalledWith("session-1", {
      answers: [{ item_id: "runtime", answer: "A process" }, { item_id: "networking", answer: "A virtual network" }],
    }));
    expect(apiMocks.assessSession).toHaveBeenCalledTimes(1);
  });

  it("disables mutations when the API has not assigned a session ID", async () => {
    apiMocks.getGoal.mockResolvedValueOnce({ goal: { id: "goal-1", title: "Containers", purpose: "Build reliable services", deadline: "2026-09-20", daily_minutes: 30, preferred_formats: ["examples"] }, concepts: [{ id: "containers", name: "Containers", importance: 1, estimated_minutes: 15, prerequisites: [] }], learner_model: { goal_id: "goal-1", concepts: {} } });
    apiMocks.getNextSession.mockResolvedValueOnce({
      id: null,
      blocks: [{ concept_id: "containers", kind: "concept", minutes: 15, objective: "Learn containers" }],
      deadline_status: "on_track",
      rationale: "Start here.",
      session_date: "2026-09-01",
      total_minutes: 15,
    });

    render(<TodaySession goalId="goal-1" goalTitle="Containers" />);

    expect(await screen.findByText("This session is not ready for feedback or follow-up requests yet.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try another explanation" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Good fit" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Needs adjustment" })).toBeDisabled();
  });
});
