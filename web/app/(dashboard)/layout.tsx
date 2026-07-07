import Sidebar from "@/components/Sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col md:flex-row">
      <Sidebar />
      <main className="flex-1 min-w-0 px-4 py-6 md:px-8 md:py-8 max-w-6xl mx-auto w-full">
        {children}
      </main>
    </div>
  );
}
