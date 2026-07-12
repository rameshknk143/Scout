"use client";

import { useEffect, useState, useTransition } from "react";
import { getAmazonStatus, connectAmazonAccount } from "@/lib/actions";

interface ConnectedAccount {
  selling_partner_id: string;
  marketplace_id: string;
  connected_at: string;
}

export default function SettingsClient() {
  const [connected, setConnected] = useState(false);
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [isPending, startTransition] = useTransition();

  // Mock settings form state for developer testing
  const [mockSellingPartnerId, setMockSellingPartnerId] = useState("A28Z9YEXAMPLE");
  const [mockCode, setMockCode] = useState("amzn1.oa.o2.code.example12345");
  const [message, setMessage] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await getAmazonStatus();
      setConnected(res.connected);
      setAccounts(res.accounts || []);
    } catch (err) {
      console.error("Failed to query Amazon connection status:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleConnectMock = () => {
    setMessage(null);
    startTransition(async () => {
      try {
        await connectAmazonAccount({
          code: mockCode,
          selling_partner_id: mockSellingPartnerId,
          marketplace_id: "A21TJRUUN4KGV",
        });
        setMessage("✅ Connection established successfully! Token registered.");
        fetchStatus();
      } catch (err: any) {
        setMessage(`❌ Error: ${err?.message || "Failed to exchange LWA tokens. Make sure LWA_CLIENT_ID env is set."}`);
      }
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-3">
        <div className="w-6 h-6 border-2 border-zinc-950 border-t-transparent rounded-full animate-spin"></div>
        <div className="text-xs text-zinc-400 font-semibold">Querying credentials status...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-zinc-900 tracking-tight">Connections & Integrations</h2>
        <p className="text-xs text-zinc-500 font-semibold mt-0.5">
          Link your Amazon India Seller account to automatically synchronize real catalog stock, sales, and transaction fees.
        </p>
      </div>

      {connected ? (
        <div className="glass-panel p-6 bg-white border-l-4 border-l-emerald-600 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded uppercase tracking-wider">
                Connected 🟢
              </span>
              <h3 className="text-sm font-bold text-zinc-950 mt-2">Amazon SP-API Active</h3>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-zinc-400 font-semibold block uppercase">Marketplace</span>
              <span className="text-xs font-bold text-zinc-700">Amazon India (aps)</span>
            </div>
          </div>

          <div className="border-t border-zinc-100 pt-4 space-y-3">
            {accounts.map((acc, index) => (
              <div key={index} className="flex justify-between items-center bg-zinc-50 p-3 rounded-lg border border-zinc-200/50">
                <div>
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Selling Partner ID</span>
                  <span className="font-mono text-xs font-bold text-zinc-800">{acc.selling_partner_id}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Linked Date</span>
                  <span className="text-xs font-semibold text-zinc-600">
                    {new Date(acc.connected_at).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" })}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <button
              onClick={() => {
                setConnected(false);
                setAccounts([]);
              }}
              className="text-[10px] font-bold text-red-600 hover:text-red-700 transition-colors uppercase tracking-wider cursor-pointer"
            >
              ⚠️ Disconnect Seller Account
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 glass-panel p-6 bg-white space-y-5">
            <div>
              <h3 className="text-sm font-bold text-zinc-900">1. Setup developer credentials</h3>
              <p className="text-xs text-zinc-500 font-semibold leading-relaxed mt-1">
                Before authorizing your seller account, you must register a developer client on the Amazon Seller Central Console (India).
                Retrieve your client credentials and add them to your <code className="font-mono bg-zinc-100 text-zinc-800 px-1 py-0.5 rounded text-[11px]">.env</code>:
              </p>
              <pre className="bg-zinc-950 text-zinc-200 text-[10px] font-mono p-3 rounded-lg mt-3 select-all leading-normal">
{`LWA_CLIENT_ID="amzn1.application-oa2-client.example..."
LWA_CLIENT_SECRET="client_secret_example_value..."`}
              </pre>
            </div>

            <div className="border-t border-zinc-100 pt-4">
              <h3 className="text-sm font-bold text-zinc-900">2. Authorize via Seller Central</h3>
              <p className="text-xs text-zinc-500 font-semibold leading-relaxed mt-1">
                Clicking authorize will redirect you to Amazon Seller Central consent page to grant catalog, order management, and financial reporting access.
              </p>
              <a
                href="https://sellercentral.amazon.in/apps/authorize/consent?application_id=amzn1.sp.id.mock-scout-app-123&state=secure_state_nonce&version=beta"
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => {
                  e.preventDefault();
                  alert("Redirecting to Amazon Developer Consent Page (OAuth LWA Endpoint Mock)...");
                }}
                className="btn-primary inline-block w-auto px-6 py-2.5 mt-3 text-xs font-bold text-center tracking-wide uppercase cursor-pointer"
              >
                🔌 Authorize Scout Integration
              </a>
            </div>
          </div>

          <div className="glass-panel p-6 bg-zinc-50/50 space-y-4">
            <div>
              <h3 className="text-sm font-bold text-zinc-900">Developer Sideload Portal</h3>
              <p className="text-[11px] text-zinc-500 font-semibold leading-relaxed mt-1">
                If you are testing locally or deploying on Vercel preview, use this portal to simulate a successful Amazon SP-API redirect.
              </p>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
                  Selling Partner ID
                </label>
                <input
                  type="text"
                  value={mockSellingPartnerId}
                  onChange={(e) => setMockSellingPartnerId(e.target.value)}
                  className="input text-zinc-900 bg-white"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-1">
                  Auth Callback Code (LWA Code)
                </label>
                <input
                  type="text"
                  value={mockCode}
                  onChange={(e) => setMockCode(e.target.value)}
                  className="input text-zinc-900 bg-white"
                />
              </div>

              <button
                onClick={handleConnectMock}
                disabled={isPending}
                className="btn-primary w-full text-center py-2 text-xs font-bold uppercase tracking-wider cursor-pointer"
              >
                {isPending ? "Exchanging Tokens..." : "⚡ Sideload credentials"}
              </button>

              {message && (
                <p className="text-[11px] font-bold mt-2 text-zinc-700 leading-normal animate-in fade-in duration-200">
                  {message}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
