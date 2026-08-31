import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DiagnosticFlow } from "@/components/DiagnosticFlow";
import type { Concept, Dashboard, LearnerModel } from "@/lib/api";

const apiMocks = vi.hoisted(() => ({ getDashboard: vi.fn(), startDiagnostic: vi.fn(), submitDiagnostic: vi.fn() }));

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, getDashboard: apiMocks.getDashboard, startDiagnostic: apiMocks.startDiagnostic, submitDiagnostic: apiMocks.submitDiagnostic };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const concepts: Concept[] = [{ id: "containers", name: "Containers", importance: 1, estimated_minutes: 15 }];
const learnerModel: LearnerModel = { goal_id: "goal-1", concepts: {} };
const dashboard: Dashboard = { deadline_status: "on_track", estimated_sessions: 2, next_review: null, on_track: true, progress: 0, projected_completion: "2026-09-20", strong: [], weak: [], why: "Start with the basics." };

describe("DiagnosticFlow", () => {
  it("posts every diagnostic answer in item order only after the final question and refreshes readiness", async () => {
    apiMocks.startDiagnostic.mockResolvedValueOnce({
      items: [
        { id: "first", concept_id: "containers", expected: "A", explanation: "", question: "First question", options: ["A"] },
        { id: "second", concept_id: "containers", expected: "B", explanation: "", question: "Second question", options: ["B"] },
      ],
    });
    let resolveSubmit: (value: { learner_model: LearnerModel }) => void = () => undefined;
    const submit = new Promise<{ learner_model: LearnerModel }>((resolve) => { resolveSubmit = resolve; });
    apiMocks.submitDiagnostic.mockReturnValueOnce(submit);
    const refreshedDashboard: Dashboard = { deadline_status: "at_risk", estimated_sessions: 7, next_review: "2026-09-03", on_track: false, progress: 0.25, projected_completion: "2026-09-25", strong: [], weak: ["containers"], why: "The diagnostic found a deeper prerequisite gap." };
    apiMocks.getDashboard.mockResolvedValueOnce(refreshedDashboard);

    render(<DiagnosticFlow goalId="goal-1" concepts={concepts} initialModel={learnerModel} dashboard={dashboard} />);
    fireEvent.click(screen.getByRole("button", { name: "Begin diagnostic" }));
    await screen.findByRole("heading", { name: "First question" });
    fireEvent.click(screen.getByRole("radio", { name: "A" }));
    fireEvent.click(screen.getByRole("button", { name: "Next question" }));

    expect(apiMocks.submitDiagnostic).not.toHaveBeenCalled();
    await screen.findByRole("heading", { name: "Second question" });
    fireEvent.click(screen.getByRole("radio", { name: "B" }));
    fireEvent.click(screen.getByRole("button", { name: "Save answer" }));

    await waitFor(() => expect(apiMocks.submitDiagnostic).toHaveBeenCalledWith("goal-1", {
      answers: [{ item_id: "first", answer: "A" }, { item_id: "second", answer: "B" }],
    }));
    expect(apiMocks.getDashboard).not.toHaveBeenCalled();
    resolveSubmit({ learner_model: learnerModel });
    await screen.findByText(refreshedDashboard.why);
    expect(apiMocks.getDashboard).toHaveBeenCalledWith("goal-1");
    expect(screen.getByText(String(refreshedDashboard.estimated_sessions))).toBeInTheDocument();
    expect(screen.getByText(refreshedDashboard.projected_completion)).toBeInTheDocument();
    expect(screen.getByText(refreshedDashboard.deadline_status)).toBeInTheDocument();
  });

  it("preserves a saved diagnostic when readiness refresh fails and retries only the dashboard", async () => {
    apiMocks.startDiagnostic.mockResolvedValueOnce({
      items: [{ id: "first", concept_id: "containers", expected: "A", explanation: "", question: "Final question", options: ["A"] }],
    });
    const acceptedModel: LearnerModel = { goal_id: "goal-1", concepts: {} };
    apiMocks.submitDiagnostic.mockResolvedValueOnce({ learner_model: acceptedModel });
    let rejectDashboard: (reason?: unknown) => void = () => undefined;
    const failedRefresh = new Promise<Dashboard>((_, reject) => { rejectDashboard = reject; });
    apiMocks.getDashboard.mockReturnValueOnce(failedRefresh);
    const refreshedDashboard: Dashboard = { deadline_status: "on_track", estimated_sessions: 3, next_review: "2026-09-04", on_track: true, progress: 0.4, projected_completion: "2026-09-22", strong: ["containers"], weak: [], why: "Your refreshed route is ready." };

    render(<DiagnosticFlow goalId="goal-1" concepts={concepts} initialModel={learnerModel} dashboard={dashboard} />);
    fireEvent.click(screen.getByRole("button", { name: "Begin diagnostic" }));
    await screen.findByRole("heading", { name: "Final question" });
    fireEvent.click(screen.getByRole("radio", { name: "A" }));
    fireEvent.click(screen.getByRole("button", { name: "Save answer" }));

    await waitFor(() => expect(apiMocks.submitDiagnostic).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(apiMocks.getDashboard).toHaveBeenCalledWith("goal-1"));
    expect(screen.queryByRole("button", { name: "Save answer" })).not.toBeInTheDocument();
    rejectDashboard(new Error("dashboard unavailable"));
    expect(await screen.findByRole("alert")).toHaveTextContent("Diagnostic saved, but readiness could not be refreshed.");
    expect(screen.queryByText(dashboard.why)).not.toBeInTheDocument();

    apiMocks.getDashboard.mockResolvedValueOnce(refreshedDashboard);
    fireEvent.click(screen.getByRole("button", { name: "Retry readiness" }));
    await screen.findByText(refreshedDashboard.why);
    expect(apiMocks.getDashboard).toHaveBeenCalledTimes(2);
    expect(apiMocks.getDashboard).toHaveBeenLastCalledWith("goal-1");
    expect(apiMocks.submitDiagnostic).toHaveBeenCalledTimes(1);
    expect(screen.queryByText("Diagnostic saved, but readiness could not be refreshed.")).not.toBeInTheDocument();
    expect(screen.getByText(String(refreshedDashboard.estimated_sessions))).toBeInTheDocument();
  });
});
