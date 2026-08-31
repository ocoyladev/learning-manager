import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DiagnosticFlow } from "@/components/DiagnosticFlow";
import type { Concept, Dashboard, LearnerModel } from "@/lib/api";

const apiMocks = vi.hoisted(() => ({ startDiagnostic: vi.fn(), submitDiagnostic: vi.fn() }));

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, startDiagnostic: apiMocks.startDiagnostic, submitDiagnostic: apiMocks.submitDiagnostic };
});

const concepts: Concept[] = [{ id: "containers", name: "Containers", importance: 1, estimated_minutes: 15 }];
const learnerModel: LearnerModel = { goal_id: "goal-1", concepts: {} };
const dashboard: Dashboard = { deadline_status: "on_track", estimated_sessions: 2, next_review: null, on_track: true, progress: 0, projected_completion: "2026-09-20", strong: [], weak: [], why: "Start with the basics." };

describe("DiagnosticFlow", () => {
  it("posts every diagnostic answer in item order only after the final question", async () => {
    apiMocks.startDiagnostic.mockResolvedValueOnce({
      items: [
        { id: "first", concept_id: "containers", expected: "A", explanation: "", question: "First question", options: ["A"] },
        { id: "second", concept_id: "containers", expected: "B", explanation: "", question: "Second question", options: ["B"] },
      ],
    });
    apiMocks.submitDiagnostic.mockResolvedValueOnce({ learner_model: learnerModel });

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
  });
});
