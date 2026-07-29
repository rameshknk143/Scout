import { Suspense } from "react";
import Sidebar from "@/components/Sidebar";
import MarketplaceIndicator from "@/components/MarketplaceIndicator";
import { SetupWizard } from "@/components/SetupWizard";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col md:flex-row min-h-screen relative bg-bg text-text">
      {/* Sidebar reads ?tab= to highlight the active entry, so it needs a
          suspense boundary or `next build` fails prerendering this layout. */}
      <Suspense fallback={<div className="w-64 shrink-0 border-r border-black/5 bg-white" />}>
        <Sidebar />
      </Suspense>

      <main className="flex-1 min-w-0 flex flex-col relative z-10">
        {/* Global Top Bar */}
        {/* The bar itself spans the full width so its border and blur reach the
            viewport edges, but its contents sit on the same max-w-6xl column as
            the page body below -- otherwise the search box and the page's <h1>
            start at two different left edges on a wide screen. */}
        <header className="sticky top-0 z-20 bg-white/85 backdrop-blur-md border-b border-black/5">
          <div className="flex items-center justify-end gap-4 px-4 md:px-8 py-3 max-w-6xl w-full mx-auto">
          {/* Quick actions, user profile */}
          <div className="flex items-center gap-3">
            {/* Marketplace Indicator */}
            <MarketplaceIndicator />

            <div className="flex items-center gap-2 border-l border-black/5 pl-3">
              <div className="w-7 h-7 rounded-full bg-zinc-100 flex items-center justify-center text-xs font-bold text-zinc-900 border border-black/10">
                RK
              </div>
              <span className="text-xs font-semibold text-zinc-700 hidden sm:inline">
                Ram
              </span>
            </div>
          </div>
          </div>
        </header>

        {/* Setup Wizard Modal for Phase 04 Onboarding */}
        <SetupWizard />

        {/* Page Content wrapper */}
        <div className="flex-1 px-4 py-6 md:px-8 md:py-8 max-w-6xl w-full mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
