import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BugPilot AI",
  description: "Evidence-backed investigation workspace",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
