import { notFound } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { DashboardControls } from "@/components/DashboardControls";
import { RationalePanel } from "@/components/RationalePanel";
import { getDashboard, getGoal, getSources } from "@/lib/api";
import { SourcePanel } from "@/components/SourcePanel";

type GoalPageProps = { params: Promise<{ id: string }> };

export default async function GoalPage({ params }: GoalPageProps) {
  const { id } = await params;
  try {
    const [details, dashboardResponse, sourceResponse] = await Promise.all([getGoal(id), getDashboard(id), getSources(id)]);
    const dashboard = dashboardResponse;
    return <AppShell goalTitle={details.goal.title}><div className="page-grid"><div className="main-rail"><div className="dashboard-intro"><div><p className="eyebrow">Mastery dashboard</p><h1>{details.goal.title}</h1><p className="lede">An auditable view of what is strong, what needs work, and why the navigator chose the next station.</p></div><div className="progress-readout"><span className="progress-value">{Math.round(dashboard.progress * 100)}%</span><span className="progress-label">Route progress</span></div></div><div className="metric-strip"><div className="metric"><strong>{dashboard.on_track ? "On track" : "Needs attention"}</strong><span>Deadline state</span></div><div className="metric"><strong>{details.goal.deadline}</strong><span>Target date</span></div><div className="metric"><strong>{dashboard.estimated_sessions}</strong><span>Sessions estimated</span></div><div className="metric"><strong>{dashboard.projected_completion}</strong><span>Projected completion</span></div></div><section className="terrain-panel" aria-labelledby="concepts-heading"><div className="section-kicker">Signal inventory</div><h2 id="concepts-heading">Concepts in view</h2><div className="concept-lists"><div><h3>Strong</h3><ul className="concept-list">{dashboard.strong.length ? dashboard.strong.map((concept) => <li key={concept}>{concept}</li>) : <li className="muted">No strong concepts yet</li>}</ul></div><div><h3>Needs work</h3><ul className="concept-list weak-list">{dashboard.weak.length ? dashboard.weak.map((concept) => <li key={concept}>{concept}</li>) : <li className="muted">Nothing flagged</li>}</ul></div></div></section><DashboardControls goalId={id} initialMinutes={details.goal.daily_minutes} /><div className="button-row" style={{ marginTop: "1rem" }}><a className="primary-action" href={`/goals/${id}/today`}>Open today&apos;s session</a></div></div><aside className="evidence-sidebar"><RationalePanel rationale={dashboard.why} deadlineStatus={dashboard.deadline_status} /><div className="readiness-panel"><div className="section-kicker">Next review</div><h2>{dashboard.next_review ?? "Not scheduled"}</h2><p className="muted">The schedule is presented from the API, with no client-side date arithmetic.</p></div><SourcePanel sources={sourceResponse.sources} /></aside></div></AppShell>;
  } catch {
    notFound();
  }
}
