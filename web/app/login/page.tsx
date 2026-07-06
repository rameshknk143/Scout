import LoginForm from "./login-form";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string }>;
}) {
  const { from } = await searchParams;
  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">🔭</div>
          <h1 className="text-2xl font-bold tracking-tight">
            <span className="text-amber">Scout</span>
          </h1>
          <p className="text-muted text-sm mt-1">Ram&apos;s personal product radar</p>
        </div>
        <LoginForm from={from || "/"} />
      </div>
    </main>
  );
}
