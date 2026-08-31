import Link from "next/link";

export default function NotFound() { return <main className="page-frame"><div className="error-message" role="alert"><h1>Learning route not found.</h1><p>That goal may have moved or never started.</p><Link className="primary-action" href="/">Start a new goal</Link></div></main>; }
