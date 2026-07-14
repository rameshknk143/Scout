import Sidebar from "@/components/Sidebar";
import MarketplaceIndicator from "@/components/MarketplaceIndicator";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col md:flex-row min-h-screen relative bg-bg text-text">
      <Sidebar />
      
      <main className="flex-1 min-w-0 flex flex-col relative z-10">
        {/* Global Top Bar */}
        <header className="sticky top-0 z-20 flex items-center justify-between px-6 py-3 bg-[#090d16]/80 backdrop-blur-md border-b border-white/5">
          {/* Left: Global Search */}
          <div className="flex items-center gap-4 flex-1 max-w-md">
            <div className="relative w-full">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-zinc-400 text-xs">
                🔍
              </span>
              <input
                type="text"
                placeholder="Search ASIN, SKU, title, brand, or keyword..."
                className="w-full text-xs bg-[#111625] border border-white/5 rounded-lg pl-8 pr-3 py-1.5 focus:outline-none focus:border-zinc-700 transition-all text-white"
              />
            </div>
          </div>

          {/* Right: Quick actions, notifications, user profile */}
          <div className="flex items-center gap-3">
            {/* Marketplace Indicator */}
            <MarketplaceIndicator />

            {/* Date Range Selector */}
            <select className="text-xs font-semibold text-zinc-300 bg-[#111625] border border-white/10 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-zinc-700 cursor-pointer">
              <option>Last 30 Days</option>
              <option>Last 7 Days</option>
              <option>Today</option>
              <option>Year to Date</option>
            </select>

            {/* Notifications Bell */}
            <button className="p-1.5 text-zinc-400 hover:text-white bg-[#111625] border border-white/10 rounded-lg relative cursor-pointer">
              🔔
              <span className="absolute top-0.5 right-0.5 block h-1.5 w-1.5 rounded-full bg-red-500" />
            </button>

            {/* User Profile */}
            <div className="flex items-center gap-2 border-l border-white/5 pl-3">
              <div className="w-7 h-7 rounded-full bg-[#111625] flex items-center justify-center text-xs font-bold text-white border border-white/10">
                RK
              </div>
              <span className="text-xs font-semibold text-zinc-300 hidden sm:inline">
                Ram
              </span>
            </div>
          </div>
        </header>

        {/* Page Content wrapper */}
        <div className="flex-1 px-4 py-6 md:px-8 md:py-8 max-w-6xl w-full mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
