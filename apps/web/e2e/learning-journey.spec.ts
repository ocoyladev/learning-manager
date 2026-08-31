import { expect, test } from "@playwright/test";

test("completes onboarding, diagnostic, session, and dashboard", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await page.getByLabel("Learning goal").fill("Learn containers");
  await page.getByLabel("Why does this matter?").fill("Build reliable services");
  await page.getByLabel("Target date").fill("2026-09-20");
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
  await page.getByRole("button", { name: "Open today's session" }).click();
  await expect(page).toHaveURL(/\/goals\/demo\/today$/);
  await expect(page.getByRole("heading", { name: "Make the next idea stick." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Why this session?" })).toBeVisible();
  await page.goto("/goals/demo");
  await expect(page.getByText("Mastery dashboard", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Sources behind the route" })).toBeVisible();
});
