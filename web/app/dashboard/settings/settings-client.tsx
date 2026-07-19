"use client";

import { useEffect, useState, useTransition } from "react";
import { getAmazonStatus, disconnectAmazonAccount } from "@/lib/actions";

interface ConnectedAccount {
  selling_partner_id: string;
  marketplace_id: string;
  connected_at: string;
}

const MARKETPLACE_NAMES: Record<string, string> = {
  "A21TJRUUN4KGV": "Amazon India",
  "ATVPDKIKX0DER": "Amazon USA",
  "A1F83G8C2ARO7P": "Amazon UK",
};

export default function SettingsClient() {
  const [connected, setConnected] = useState(false);
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [isPending, startTransition] = useTransition();

  const [marketplaceId, setMarketplaceId] = useState("A21TJRUUN4KGV");
  const [message, setMessage] = useState<string | null>(null);

  // Sends the seller to Amazon Seller Central's consent page. On approval Amazon
  // redirects back to /auth/amazon/callback with the authorization code, which
  // the backend exchanges for a refresh token. `version=beta` keeps this working
  // for a Draft app authorizing its own seller account (drop it once published).
  const getAuthorizeUrl = () => {
    const domain =
      marketplaceId === "ATVPDKIKX0DER"
        ? "sellercentral.amazon.com"
        : marketplaceId === "A1F83G8C2ARO7P"
          ? "sellercentral-europe.amazon.com"
          : "sellercentral.amazon.in";
    const appId = process.env.NEXT_PUBLIC_AMAZON_APP_ID || "";
    return `https://${domain}/apps/authorize/consent?application_id=${appId}&state=${marketplaceId}&version=beta`;
  };

  const appConfigured = Boolean(process.env.NEXT_PUBLIC_AMAZON_APP_ID);

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

  const handleDisconnect = async () => {
    setMessage(null);
    startTransition(async () => {
      try {
        for (const acc of accounts) {
          await disconnectAmazonAccount(acc.selling_partner_id);
        }
        setMessage("Disconnected. Your stored Amazon access token has been removed.");
        fetchStatus();
      } catch (err: any) {
        setMessage(`Couldn't disconnect: ${err?.message || "please try again."}`);
      }
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-3">
        <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
        <div className="text-xs text-zinc-500 font-semibold font-mono">Checking your Amazon connection…</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight font-sans">Connections</h2>
        <p className="text-xs text-zinc-400 font-semibold mt-0.5">
          Link your Amazon Seller account to sync your real sales, orders, and fees into ScoutVeda.
        </p>
      </div>

      {connected ? (
        <div className="glass-panel p-6 bg-white border border-black/5 border-l-4 border-l-emerald-500 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-2 py-0.5 rounded uppercase tracking-wider">
                Connected 🟢
              </span>
              <h3 className="text-sm font-bold text-zinc-900 mt-2">Amazon Seller account linked</h3>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-zinc-500 font-semibold block uppercase">Marketplace</span>
              <span className="text-xs font-bold text-zinc-700">
                {MARKETPLACE_NAMES[accounts[0]?.marketplace_id] || accounts[0]?.marketplace_id || "Amazon India"}
              </span>
            </div>
          </div>

          <div className="border-t border-black/5 pt-4 space-y-3">
            {accounts.map((acc, index) => (
              <div key={index} className="flex justify-between items-center bg-zinc-50 p-3 rounded-lg border border-black/5">
                <div>
                  <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Selling Partner ID</span>
                  <span className="font-mono text-xs font-bold text-zinc-700">{acc.selling_partner_id}</span>
                </div>
                <div className="text-right flex items-center gap-6">
                  <div>
                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Region</span>
                    <span className="font-mono text-xs font-bold text-zinc-700">{MARKETPLACE_NAMES[acc.marketplace_id] || acc.marketplace_id}</span>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block">Linked</span>
                    <span className="text-xs font-semibold text-zinc-500 font-mono">
                      {new Date(acc.connected_at).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <button
              onClick={handleDisconnect}
              disabled={isPending}
              className="text-[10px] font-bold text-red-500 hover:text-red-600 transition-colors uppercase tracking-wider cursor-pointer disabled:opacity-50"
            >
              {isPending ? "Disconnecting…" : "Disconnect Amazon account"}
            </button>
          </div>
          {message && (
            <p className="text-[11px] font-bold mt-2 text-zinc-650 leading-normal">{message}</p>
          )}
        </div>
      ) : (
        <div className="glass-panel p-6 bg-white border border-black/5 shadow-sm space-y-5">
          <div className="flex items-start gap-4">
            <div className="text-3xl leading-none">🔗</div>
            <div>
              <h3 className="text-sm font-bold text-zinc-900">Connect your Amazon Seller account</h3>
              <p className="text-xs text-zinc-500 font-semibold leading-relaxed mt-1">
                You'll be sent to Amazon Seller Central to approve access. ScoutVeda never sees your Amazon
                password — Amazon returns a secure access token that we store encrypted and use only to read
                your sales, orders, and fees.
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-1 w-full max-w-xs">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Marketplace</label>
            <select
              value={marketplaceId}
              onChange={(e) => setMarketplaceId(e.target.value)}
              className="w-full text-xs font-semibold text-zinc-300 bg-[#181d2c] border border-white/10 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700 cursor-pointer"
            >
              <option value="A21TJRUUN4KGV">🇮🇳 Amazon India</option>
              <option value="ATVPDKIKX0DER">🇺🇸 Amazon USA</option>
              <option value="A1F83G8C2ARO7P">🇬🇧 Amazon UK</option>
            </select>
          </div>

          {appConfigured ? (
            <a
              href={getAuthorizeUrl()}
              className="btn-primary inline-block w-auto px-6 py-2.5 text-xs font-bold text-center tracking-wide uppercase cursor-pointer"
            >
              🔌 Connect Amazon Account
            </a>
          ) : (
            <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3">
              <p className="text-[11px] font-bold text-amber-300 leading-relaxed">
                Amazon connection isn't switched on yet. The app's SP-API credentials still need to be
                configured on the server before this button can link a live account.
              </p>
            </div>
          )}

          <p className="text-[11px] text-zinc-500 font-semibold">
            Secure OAuth through Amazon Seller Central. You can disconnect anytime.
          </p>
          {message && (
            <p className="text-[11px] font-bold mt-1 text-zinc-300 leading-normal">{message}</p>
          )}
        </div>
      )}
    </div>
  );
}
