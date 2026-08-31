import { expect, test } from "@playwright/test";

function futureDate(): string {
  const date = new Date();
  date.setUTCDate(date.getUTCDate() + 7);
  return date.toISOString().slice(0, 10);
}

test("completes onboarding, diagnostic, session, and dashboard", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await page.getByLabel("Learning goal").fill("Learn containers");
  await page.getByLabel("Why does this matter?").fill("Build reliable services");
  await page.getByLabel("Target date").fill(futureDate());
  await page.getByLabel("Minutes per day").fill("30");
  await page.getByLabel("Hands-on examples").check();
  await Promise.all([
    page.waitForURL(/\/goals\/demo\/diagnostic$/, { timeout: 20_000, waitUntil: "commit" }),
    page.getByRole("button", { name: "Create learning route" }).click(),
  ]);
  await page.getByRole("button", { name: "Begin diagnostic" }).click();
  await expect(page.getByRole("heading", { name: "What does a container isolate?" })).toBeVisible();
  await page.getByLabel("Process and dependencies").check();
  await page.getByRole("button", { name: "Save answer" }).click();
  await expect(page.getByRole("heading", { name: "Knowledge map" })).toBeVisible();
  await page.getByRole("link", { name: "View dashboard" }).click();
  await expect(page.getByText("Mastery dashboard", { exact: true })).toBeVisible();
  await page.route("**/api/goals/demo/next-session*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "session-demo",
        session_date: new Date().toISOString().slice(0, 10),
        total_minutes: 25,
        rationale: "Retrieve the weak point, then reinforce it with a concise explanation.",
        deadline_status: "on_track",
        reviews_included: [],
        deferred_concepts: [],
        blocks: [
          { concept_id: "containers-basics", kind: "retrieval", minutes: 10, objective: "Recall container isolation" },
          { concept_id: "containers-basics", kind: "concept", minutes: 15, objective: "Reinforce container isolation", content: "A container isolates a process and its dependencies while sharing the host kernel.", source_ids: ["source-official"] },
        ],
      }),
    });
  });
  await page.getByRole("link", { name: "Open today's session" }).click();
  await expect(page).toHaveURL(/\/goals\/demo\/today$/);
  await expect(page.getByRole("heading", { name: "Make the next idea stick." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Why this session?" })).toBeVisible();
  await page.getByLabel("Write your answer from memory").fill("A process and its dependencies");
  await page.getByRole("button", { name: "Submit assessment" }).click();
  await expect(page.getByRole("heading", { name: "What the assessor recorded" })).toBeVisible();
  await expect(page.getByText("Correctly explained process and dependency isolation.")).toBeVisible();
  await page.getByRole("button", { name: "Try another explanation" }).click();
  await expect(page.getByText("A container packages an application and its dependencies while sharing the host kernel.")).toBeVisible();
  await page.getByRole("button", { name: "Good fit" }).click();
  await expect(page.getByText("Session feedback recorded.")).toBeVisible();
  await page.getByRole("link", { name: "Back to dashboard" }).click();
  await expect(page.getByText("Mastery dashboard", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Sources behind the route" })).toBeVisible();
  await page.getByRole("button", { name: "Save availability" }).click();
  await expect(page.getByText("Daily availability saved.")).toBeVisible();
});
