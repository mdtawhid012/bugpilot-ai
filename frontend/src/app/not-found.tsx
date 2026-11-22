import Link from "next/link";

export default function NotFound() {
  return (
    <main className="page-container">
      <div className="empty-state">
        <h1>Page not found</h1>
        <p>The requested BugPilot page does not exist.</p>
        <Link className="button" href="/">Return to overview</Link>
      </div>
    </main>
  );
}
