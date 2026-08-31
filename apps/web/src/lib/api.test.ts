import { afterEach, describe, expect, it, vi } from "vitest";
import { createGoal } from "@/lib/api";
import type { GoalRequest } from "@/lib/api";

afterEach(() => vi.restoreAllMocks());

describe("api mutations", () => {
  it("does not replay a mutation when a successful response has malformed JSON", async () => {
    const request: GoalRequest = {
      title: "Learn containers",
      purpose: "Build reliable services",
      deadline: "2026-09-20",
      daily_minutes: 30,
      preferred_formats: ["examples"],
    };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{", { status: 200, headers: { "Content-Type": "application/json" } }));

    await expect(createGoal(request)).rejects.toThrow();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
