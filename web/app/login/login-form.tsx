"use client";

import { useActionState } from "react";
import { login } from "@/lib/auth-actions";

export default function LoginForm({ from }: { from: string }) {
  const [state, formAction, pending] = useActionState(login, undefined);

  return (
    <form action={formAction} className="glass-panel p-6 space-y-4">
      <input type="hidden" name="from" value={from} />
      <div>
        <label htmlFor="password" className="block text-sm text-muted mb-2">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoFocus
          required
          className="w-full rounded-lg bg-white/5 border border-white/10 px-4 py-2.5 text-text outline-none focus:border-amber/60 focus:ring-1 focus:ring-amber/40 transition-colors"
        />
      </div>
      {state?.error && (
        <p className="text-red text-sm">{state.error}</p>
      )}
      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-lg bg-amber text-black font-semibold py-2.5 transition-opacity hover:opacity-90 disabled:opacity-50"
      >
        {pending ? "Checking…" : "Enter"}
      </button>
    </form>
  );
}
