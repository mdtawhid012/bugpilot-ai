import Link from "next/link";
import { Activity, LayoutDashboard, Plus, Settings } from "lucide-react";

export function AppSidebar() {
  return (
    <aside className="sidebar">
      <Link href="/" className="brand" aria-label="BugPilot AI overview">
        <span className="brand-mark">B</span>
        <span>BugPilot</span>
      </Link>
      <nav className="sidebar-nav" aria-label="Primary navigation">
        <Link href="/"><LayoutDashboard size={17} />Overview</Link>
        <Link href="/investigations"><Activity size={17} />Investigations</Link>
        <Link href="/investigations/new"><Plus size={17} />New investigation</Link>
      </nav>
      <div className="sidebar-footer">
        <button className="sidebar-placeholder" type="button" disabled title="Settings unavailable in Stage 1"><Settings size={17} />Settings</button>
      </div>
    </aside>
  );
}
