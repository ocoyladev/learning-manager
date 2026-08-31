import { render, screen } from "@testing-library/react";
import { createElement } from "react";
import { describe, expect, it } from "vitest";
import { RationalePanel } from "@/components/RationalePanel";

describe("RationalePanel", () => {
  it("makes the planner decision and supporting signals explicit", () => {
    render(createElement(RationalePanel, { rationale: "Build the prerequisite foundation first.", deadlineStatus: "on_track", reviewsIncluded: ["containers-basics"], deferredConcepts: ["advanced-networking"] }));
    expect(screen.getByRole("heading", { name: "Why this session?" })).toBeInTheDocument();
    expect(screen.getByText("Build the prerequisite foundation first.")).toBeInTheDocument();
    expect(screen.getByText("on track")).toBeInTheDocument();
    expect(screen.getByText("containers-basics")).toBeInTheDocument();
    expect(screen.getByText("advanced-networking")).toBeInTheDocument();
  });
});
