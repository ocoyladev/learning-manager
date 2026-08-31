import { AppShell } from "@/components/AppShell";
import { GoalForm } from "@/components/GoalForm";

export default function HomePage() {
  return <AppShell><div className="form-wrap"><div className="onboarding-intro"><div><p className="eyebrow">A persistent learning navigator</p><h1 id="learning-manager-heading">Build knowledge that holds.</h1></div><p className="lede">Turn a technical ambition into a visible route: one decision, one piece of evidence, one next session at a time.</p></div><GoalForm /></div></AppShell>;
}
