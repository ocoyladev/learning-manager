import type { components, operations } from "./api-types";

export type Goal = components["schemas"]["LearningGoal"];
export type Concept = components["schemas"]["Concept"];
export type LearnerModel = components["schemas"]["LearnerModel"];
export type LearnerConceptState = components["schemas"]["LearnerConceptState"];
export type Session = components["schemas"]["NextSessionDecision"];
export type SessionBlock = components["schemas"]["SessionBlock"];
export type AssessmentItem = components["schemas"]["AssessmentItem"];
export type Source = components["schemas"]["Source"];
export type Dashboard = components["schemas"]["_DashboardResponse"];
export type GoalRequest = components["schemas"]["_GoalRequest"];
export type AnswersRequest = components["schemas"]["_AnswersRequest"];
export type AssessmentResponse = components["schemas"]["_AssessmentResponse"];
export type AcceptedResponse = components["schemas"]["_AcceptedResponse"];
export type GoalUpdateRequest = components["schemas"]["_GoalUpdateRequest"];
export type SessionFeedbackRequest = components["schemas"]["_SessionFeedbackRequest"];

type SuccessResponse<Operation extends keyof operations> =
  operations[Operation]["responses"][200]["content"]["application/json"];

type RequestBody<Operation extends keyof operations> = operations[Operation] extends {
  requestBody: { content: { "application/json": infer Body } };
}
  ? Body
  : never;

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function errorMessage(payload: unknown, fallback: string): string {
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = payload.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (typeof first === "object" && first !== null && "msg" in first && typeof first.msg === "string") {
        return first.msg;
      }
    }
  }
  return fallback;
}

const API_BASE =
  typeof window === "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "/backend";

async function call<Operation extends keyof operations>(
  operation: Operation,
  path: string,
  method: "GET" | "POST" | "PATCH",
  body?: RequestBody<Operation>,
): Promise<SuccessResponse<Operation>> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => undefined);
    throw new ApiError(response.status, errorMessage(payload, `Request failed (${response.status})`));
  }

  try {
    return await response.json();
  } catch (error: unknown) {
    if (error instanceof SyntaxError) {
      await new Promise((resolve) => setTimeout(resolve, 50));
      const retry = await fetch(`${API_BASE}${path}`, {
        method,
        headers: body === undefined ? undefined : { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
        cache: "no-store",
      });
      if (!retry.ok) {
        const payload: unknown = await retry.json().catch(() => undefined);
        throw new ApiError(retry.status, errorMessage(payload, `Request failed (${retry.status})`));
      }
      return retry.json();
    }
    throw error;
  }
}

export function createGoal(body: GoalRequest) {
  return call("create_goal_goals_post", "/goals", "POST", body);
}

export function getGoal(goalId: string) {
  return call("get_goal_goals__goal_id__get", `/goals/${encodeURIComponent(goalId)}`, "GET");
}

export function updateGoal(goalId: string, body: GoalUpdateRequest) {
  return call("update_goal_goals__goal_id__patch", `/goals/${encodeURIComponent(goalId)}`, "PATCH", body);
}

export function getDashboard(goalId: string) {
  return call("dashboard_goals__goal_id__dashboard_get", `/goals/${encodeURIComponent(goalId)}/dashboard`, "GET");
}

export function startDiagnostic(goalId: string) {
  return call("diagnostic_goals__goal_id__diagnostic_post", `/goals/${encodeURIComponent(goalId)}/diagnostic`, "POST");
}

export function submitDiagnostic(goalId: string, body: AnswersRequest) {
  return call("diagnostic_answers_goals__goal_id__diagnostic_answers_post", `/goals/${encodeURIComponent(goalId)}/diagnostic/answers`, "POST", body);
}

export function getNextSession(goalId: string, today: string) {
  return call("next_session_goals__goal_id__next_session_get", `/goals/${encodeURIComponent(goalId)}/next-session?today=${encodeURIComponent(today)}`, "GET");
}

export function rejectRecommendation(goalId: string, reason: string) {
  return call("reject_recommendation_goals__goal_id__recommendations_reject_post", `/goals/${encodeURIComponent(goalId)}/recommendations/reject`, "POST", { reason });
}

export function getSources(goalId: string) {
  return call("sources_goals__goal_id__sources_get", `/goals/${encodeURIComponent(goalId)}/sources`, "GET");
}

export function assessSession(sessionId: string, body: AnswersRequest) {
  return call("assess_sessions__session_id__assess_post", `/sessions/${encodeURIComponent(sessionId)}/assess`, "POST", body);
}

export function sendSessionFeedback(sessionId: string, body: SessionFeedbackRequest) {
  return call("session_feedback_sessions__session_id__feedback_post", `/sessions/${encodeURIComponent(sessionId)}/feedback`, "POST", body);
}

export function requestAlternativeExplanation(sessionId: string) {
  return call("alternative_explanation_sessions__session_id__alternative_explanation_post", `/sessions/${encodeURIComponent(sessionId)}/alternative-explanation`, "POST");
}
