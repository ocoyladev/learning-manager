import Link from "next/link";

type AppShellProps = {
  children: React.ReactNode;
  goalTitle?: string;
  eyebrow?: string;
};

export function AppShell({ children, goalTitle, eyebrow = "Learning Manager" }: AppShellProps) {
  return (
    <div className="app-frame">
      <header className="topbar">
        <Link className="brand" href="/" aria-label="Learning Manager home">
          <span className="brand-mark" aria-hidden="true">LM</span>
          <span>{eyebrow}</span>
        </Link>
        {goalTitle ? <div className="goal-context"><span>Current route</span><strong>{goalTitle}</strong></div> : null}
        <nav aria-label="Primary navigation" className="topnav">
          <Link href="/">New goal</Link>
          {goalTitle ? <span aria-current="page">Active journey</span> : null}
        </nav>
      </header>
      <main className="page-frame" id="main-content" tabIndex={-1}>{children}</main>
    </div>
  );
}
