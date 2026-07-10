import Sidebar from "@/components/Sidebar";
import Dashboard3DBackground from "@/components/3d/DashboardBackground";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col md:flex-row min-h-screen relative bg-[#f9f9fb]">
      <Dashboard3DBackground />
      <Sidebar />
      
      <main className="flex-1 min-w-0 flex flex-col relative z-10">
        {/* Global Top Bar */}
        <header className="sticky top-0 z-20 flex items-center justify-between px-6 py-3 bg-white/80 backdrop-blur-md border-b border-zinc-200/60">
          {/* Left: Global Search */}
          <div className="flex items-center gap-4 flex-1 max-w-md">
            <div className="relative w-full">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-zinc-400 text-xs">
                🔍
              </span>
              <input
                type="text"
                placeholder="Search ASIN, SKU, title, brand, or keyword..."
                className="w-full text-xs bg-zinc-50 border border-zinc-200/80 rounded-lg pl-8 pr-3 py-1.5 focus:outline-none focus:border-zinc-400 focus:bg-white transition-all text-zinc-900"
              />
            </div>
          </div>

          {/* Right: Quick actions, notifications, user profile */}
          <div className="flex items-center gap-3">
            {/* Marketplace Indicator */}
            <span className="hidden md:inline-flex items-center text-[10px] font-bold text-zinc-500 bg-zinc-100 border border-zinc-200 px-2 py-1 rounded">
              🇮🇳 AMAZON.IN
            </span>

            {/* Date Range Selector */}
            <select className="text-xs font-semibold text-zinc-600 bg-zinc-50 border border-zinc-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-zinc-400 cursor-pointer">
              <option>Last 30 Days</option>
              <option>Last 7 Days</option>
              <option>Today</option>
              <option>Year to Date</option>
            </select>

            {/* Notifications Bell */}
            <button className="p-1.5 text-zinc-500 hover:text-zinc-900 bg-zinc-50 hover:bg-zinc-100 border border-zinc-200 rounded-lg relative cursor-pointer">
              🔔
              <span className="absolute top-0.5 right-0.5 block h-1.5 w-1.5 rounded-full bg-red-600" />
            </button>

            {/* User Profile */}
            <div className="flex items-center gap-2 border-l border-zinc-200 pl-3">
              <div className="w-7 h-7 rounded-full bg-zinc-100 flex items-center justify-center text-xs font-bold text-zinc-700 border border-zinc-200">
                RK
              </div>
              <span className="text-xs font-semibold text-zinc-700 hidden sm:inline">
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
