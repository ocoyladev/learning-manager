import { render, screen } from "@testing-library/react";
import { createElement } from "react";
import { describe, expect, it } from "vitest";
import { KnowledgeMap } from "@/components/KnowledgeMap";
import type { Concept, LearnerModel } from "@/lib/api";

const concepts: Concept[] = [
  { id: "foundations", name: "Foundations", prerequisites: [], importance: 1, estimated_minutes: 15 },
  { id: "delivery", name: "Delivery", prerequisites: ["foundations"], importance: 0.8, estimated_minutes: 20 },
];

const learnerModel: LearnerModel = {
  goal_id: "demo",
  concepts: {
    foundations: { concept_id: "foundations", mastery: 0.92, confidence: 0.9, state: "mastered" },
    delivery: { concept_id: "delivery", mastery: 0.25, confidence: 0.35, state: "weak" },
  },
};

describe("KnowledgeMap", () => {
  it("exposes ordered stations with accessible mastery bars and state", () => {
    render(createElement(KnowledgeMap, { concepts, learnerModel }));
    expect(screen.getByRole("heading", { name: "Knowledge map" })).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "Foundations mastery" })).toHaveAttribute("aria-valuenow", "0.92");
    expect(screen.getByText("mastered")).toBeInTheDocument();
    expect(screen.getByText("weak")).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "Delivery mastery" })).toHaveAttribute("aria-valuenow", "0.25");
  });
});
