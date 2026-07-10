import Sidebar from "@/components/Sidebar";
import Dashboard3DBackground from "@/components/3d/DashboardBackground";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col md:flex-row min-h-screen relative">
      <Dashboard3DBackground />
      <Sidebar />
      <main className="flex-1 min-w-0 px-4 py-6 md:px-8 md:py-8 max-w-6xl mx-auto w-full relative z-10">
        {children}
      </main>
    </div>
  );
}
