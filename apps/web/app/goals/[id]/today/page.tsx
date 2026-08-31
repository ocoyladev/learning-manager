import { notFound } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { getGoal, isNotFoundError } from "@/lib/api";
import { TodaySession } from "@/components/TodaySession";

type TodayPageProps = { params: Promise<{ id: string }> };

export default async function TodayPage({ params }: TodayPageProps) {
  const { id } = await params;
  try {
    const details = await getGoal(id);
    return <AppShell goalTitle={details.goal.title}><TodaySession goalId={id} goalTitle={details.goal.title} /></AppShell>;
  } catch (error: unknown) {
    if (isNotFoundError(error)) notFound();
    throw error;
  }
}
