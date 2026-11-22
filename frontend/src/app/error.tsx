"use client";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="page-container">
      <div className="error-state" role="alert">
        <strong>BugPilot could not render this page</strong>
        <p>{error.message}</p>
        <button className="button secondary" onClick={reset}>Try again</button>
      </div>
    </main>
  );
}
