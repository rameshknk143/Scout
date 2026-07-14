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
  const [marketplaceId, setMarketplaceId] = useState("A21TJRUUN4KGV");
  const [message, setMessage] = useState<string | null>(null);

  const MARKETPLACE_NAMES: Record<string, string> = {
    "A21TJRUUN4KGV": "Amazon India",
    "ATVPDKIKX0DER": "Amazon USA",
    "A1F83G8C2ARO7P": "Amazon UK",
  };

  const getAuthorizeUrl = () => {
    const domain = marketplaceId === "ATVPDKIKX0DER"
      ? "sellercentral.amazon.com"
      : marketplaceId === "A1F83G8C2ARO7P"
        ? "sellercentral-europe.amazon.com"
        : "sellercentral.amazon.in";
    return `https://${domain}/apps/authorize/consent?application_id=amzn1.sp.id.mock-scout-app-123&state=secure_state_nonce&version=beta`;
  };

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
          marketplace_id: marketplaceId,
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
        <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        <div className="text-xs text-zinc-500 font-semibold font-mono animate-pulse">Querying credentials status...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight font-sans">Connections & Integrations</h2>
        <p className="text-xs text-zinc-400 font-semibold mt-0.5">
          Link your Amazon Seller account (India, USA, UK) to automatically synchronize real catalog stock, sales, and transaction fees.
        </p>
      </div>

      {connected ? (
        <div className="glass-panel p-6 bg-[#111625] border-l-4 border-l-emerald-500 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded uppercase tracking-wider">
                Connected 🟢
              </span>
              <h3 className="text-sm font-bold text-white mt-2">Amazon SP-API Active</h3>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-zinc-500 font-semibold block uppercase">Marketplace</span>
              <span className="text-xs font-bold text-zinc-300">
                {MARKETPLACE_NAMES[accounts[0]?.marketplace_id] || accounts[0]?.marketplace_id || "Amazon India"}
              </span>
            </div>
          </div>

          <div className="border-t border-white/5 pt-4 space-y-3">
            {accounts.map((acc, index) => (
              <div key={index} className="flex justify-between items-center bg-[#181d2c]/50 p-3 rounded-lg border border-white/5">
                <div>
                  <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Selling Partner ID</span>
                  <span className="font-mono text-xs font-bold text-zinc-300">{acc.selling_partner_id}</span>
                </div>
                <div className="text-right flex items-center gap-6">
                  <div>
                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Region</span>
                    <span className="font-mono text-xs font-bold text-zinc-300">{MARKETPLACE_NAMES[acc.marketplace_id] || acc.marketplace_id}</span>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Linked Date</span>
                    <span className="text-xs font-semibold text-zinc-400 font-mono">
                      {new Date(acc.connected_at).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" })}
                    </span>
                  </div>
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
              className="text-[10px] font-bold text-red-400 hover:text-red-500 transition-colors uppercase tracking-wider cursor-pointer"
            >
              ⚠️ Disconnect Seller Account
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 glass-panel p-6 bg-[#111625] space-y-5">
            <div>
              <h3 className="text-sm font-bold text-white">1. Setup developer credentials</h3>
              <p className="text-xs text-zinc-400 font-semibold leading-relaxed mt-1">
                Before authorizing your seller account, you must register a developer client on the Amazon Seller Central Console.
                Retrieve your client credentials and add them to your <code className="font-mono bg-[#181d2c] border border-white/5 text-zinc-300 px-1 py-0.5 rounded text-[11px]">.env</code>:
              </p>
              <pre className="bg-[#090d16] border border-white/5 text-zinc-300 text-[10px] font-mono p-3 rounded-lg mt-3 select-all leading-normal">
{`LWA_CLIENT_ID="amzn1.application-oa2-client.example..."
LWA_CLIENT_SECRET="client_secret_example_value..."`}
              </pre>
            </div>

            <div className="border-t border-white/5 pt-4 space-y-4">
              <h3 className="text-sm font-bold text-white">2. Authorize via Seller Central</h3>
              
              <div className="flex flex-col gap-1 w-64">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Target Marketplace</label>
                <select
                  value={marketplaceId}
                  onChange={(e) => setMarketplaceId(e.target.value)}
                  className="w-full text-xs font-semibold text-zinc-300 bg-[#181d2c] border border-white/10 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700 cursor-pointer"
                >
                  <option value="A21TJRUUN4KGV">🇮🇳 Amazon India (A21TJRUUN4KGV)</option>
                  <option value="ATVPDKIKX0DER">🇺🇸 Amazon USA (ATVPDKIKX0DER)</option>
                  <option value="A1F83G8C2ARO7P">🇬🇧 Amazon UK (A1F83G8C2ARO7P)</option>
                </select>
              </div>

              <p className="text-xs text-zinc-400 font-semibold leading-relaxed mt-1">
                Clicking authorize will redirect you to Amazon Seller Central consent page to grant catalog, order management, and financial reporting access.
              </p>
              <a
                href={getAuthorizeUrl()}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => {
                  e.preventDefault();
                  alert(`Redirecting to Amazon Developer Consent Page for ${MARKETPLACE_NAMES[marketplaceId]} (OAuth LWA Endpoint Mock)...`);
                }}
                className="btn-primary inline-block w-auto px-6 py-2.5 mt-3 text-xs font-bold text-center tracking-wide uppercase cursor-pointer"
              >
                🔌 Authorize Scout Integration
              </a>
            </div>
          </div>

          <div className="glass-panel p-6 bg-[#111625]/20 border border-white/5 space-y-4">
            <div>
              <h3 className="text-sm font-bold text-white">Developer Sideload Portal</h3>
              <p className="text-[11px] text-zinc-400 font-semibold leading-relaxed mt-1">
                If you are testing locally or deploying on Vercel preview, use this portal to simulate a successful Amazon SP-API redirect.
              </p>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">
                  Target Marketplace
                </label>
                <select
                  value={marketplaceId}
                  onChange={(e) => setMarketplaceId(e.target.value)}
                  className="w-full text-xs font-semibold text-zinc-300 bg-[#181d2c] border border-white/10 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700 cursor-pointer mb-2"
                >
                  <option value="A21TJRUUN4KGV">🇮🇳 Amazon India (A21TJRUUN4KGV)</option>
                  <option value="ATVPDKIKX0DER">🇺🇸 Amazon USA (ATVPDKIKX0DER)</option>
                  <option value="A1F83G8C2ARO7P">🇬🇧 Amazon UK (A1F83G8C2ARO7P)</option>
                </select>

                <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">
                  Selling Partner ID
                </label>
                <input
                  type="text"
                  value={mockSellingPartnerId}
                  onChange={(e) => setMockSellingPartnerId(e.target.value)}
                  className="input text-white bg-[#181d2c]"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">
                  Auth Callback Code (LWA Code)
                </label>
                <input
                  type="text"
                  value={mockCode}
                  onChange={(e) => setMockCode(e.target.value)}
                  className="input text-white bg-[#181d2c]"
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
                <p className="text-[11px] font-bold mt-2 text-zinc-300 leading-normal animate-in fade-in duration-200">
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
