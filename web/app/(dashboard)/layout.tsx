import Sidebar from "@/components/Sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 min-w-0 px-8 py-8 max-w-6xl mx-auto w-full">
        {children}
      </main>
    </div>
  );
}
