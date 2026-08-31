import { notFound } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { DiagnosticFlow } from "@/components/DiagnosticFlow";
import { getDashboard, getGoal, isNotFoundError } from "@/lib/api";

type DiagnosticPageProps = { params: Promise<{ id: string }> };

export default async function DiagnosticPage({ params }: DiagnosticPageProps) {
  const { id } = await params;
  try {
    const [details, dashboard] = await Promise.all([getGoal(id), getDashboard(id)]);
    return <AppShell goalTitle={details.goal.title}><div className="page-grid"><div className="main-rail"><p className="eyebrow">First signal · diagnostic</p><h1>Find your starting station.</h1><p className="lede">One focused question gives the navigator evidence about where to begin. Answer from memory; this is a baseline, not a test.</p><DiagnosticFlow goalId={id} concepts={details.concepts} initialModel={details.learner_model} dashboard={dashboard} /></div><aside className="evidence-sidebar"><div className="readiness-panel"><div className="section-kicker">Route preview</div><h2>Goal readiness</h2><p className="muted">The API will refine this estimate after your diagnostic.</p><div className="readiness-grid"><div><span className="readiness-value">{dashboard.estimated_sessions}</span><span className="readiness-label">Sessions</span></div><div><span className="readiness-value">{details.goal.daily_minutes}m</span><span className="readiness-label">Daily time</span></div><div><span className="readiness-value">{dashboard.projected_completion}</span><span className="readiness-label">Projected</span></div></div></div></aside></div></AppShell>;
  } catch (error: unknown) {
    if (isNotFoundError(error)) notFound();
    throw error;
  }
}
