"use client";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) { return <main className="page-frame"><div className="error-message" role="alert"><h1>That route needs another look.</h1><p>The learning service did not return a usable response.</p><button className="primary-action" type="button" onClick={reset}>Try again</button></div></main>; }
