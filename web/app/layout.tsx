import type { Metadata } from "next";
import "./globals.css";
import { ThemeBootstrapScript } from "@/components/ThemeToggle";

export const metadata: Metadata = {
  title: "ScoutVeda",
  description: "Find products worth sourcing — KNK Enterprises",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        {/* Runs before paint so the theme is correct on first render — no flash */}
        <ThemeBootstrapScript />
      </head>
      <body className="min-h-full bg-surface-0 text-text-primary" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
