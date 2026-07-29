"use client";

import { useEffect, useState, useTransition } from "react";
import { getAmazonStatus, disconnectAmazonAccount, getSaasAuditLogs, getSaasOrgMembers, addSaasOrgMember } from "@/lib/actions";

interface ConnectedAccount {
  selling_partner_id: string;
  marketplace_id: string;
  connected_at: string;
}

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: "Owner" | "Admin" | "Analyst" | "Viewer";
  joinedAt: string;
  avatar: string;
}

interface AuditLogItem {
  id: string;
  actor: string;
  action: string;
  target: string;
  timestamp: string;
  ip: string;
}

const MARKETPLACE_NAMES: Record<string, string> = {
  "A21TJRUUN4KGV": "Amazon India",
  "ATVPDKIKX0DER": "Amazon USA",
  "A1F83G8C2ARO7P": "Amazon UK",
  "A1PA6795UKMFR9": "Amazon Germany",
  "A13V1IB3VIYZZH": "Amazon France",
  "APJ6JRA9NG5V4": "Amazon Italy",
  "A1RKKUPIHCS9HS": "Amazon Spain",
  "A2EUQ1WTGCTBG2": "Amazon Canada",
  "A39IBJ37TRP1C6": "Amazon Australia",
  "A1VC38T7YXB528": "Amazon Japan",
  "A1AM78C64UM0Y8": "Amazon Mexico",
  "A2VIGQ35RCS4UG": "Amazon UAE",
};

// Plan limits — product constants, not measured data.
// No plan caps are defined here on purpose. There is no billing system and no
// subscription tier, so any "x of N used" figure would be an invented limit.

export default function SettingsClient() {
  const [activeTab, setActiveTab] = useState<"connections" | "teams" | "usage" | "audit">("connections");
  const [connected, setConnected] = useState(false);
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [isPending, startTransition] = useTransition();

  const [marketplaceId, setMarketplaceId] = useState("A21TJRUUN4KGV");
  const [message, setMessage] = useState<string | null>(null);

  // Team Invite State
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"Admin" | "Analyst" | "Viewer">("Analyst");
  const [inviteStatus, setInviteStatus] = useState<string | null>(null);
  const [inviteFailed, setInviteFailed] = useState(false);

  const [members, setMembers] = useState<TeamMember[]>([]);
  const [membersError, setMembersError] = useState<string | null>(null);

  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [auditError, setAuditError] = useState<string | null>(null);

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
    }

    try {
      setAuditError(null);
      const dbLogs = await getSaasAuditLogs();
      setAuditLogs(
        (dbLogs?.logs ?? []).map((l: any) => ({
          id: String(l.id),
          actor: l.actor_email,
          action: l.action,
          target: l.target,
          timestamp: l.created_at.slice(0, 16).replace("T", " "),
          ip: l.ip_address || "—",
        }))
      );
    } catch (err: any) {
      console.error("Failed to load audit logs:", err);
      setAuditLogs([]);
      setAuditError(err?.message || "Could not load audit logs.");
    }

    try {
      setMembersError(null);
      const dbMembers = await getSaasOrgMembers();
      setMembers(
        (dbMembers?.members ?? []).map((m: any) => ({
          id: String(m.id),
          name: m.name || m.email.split("@")[0],
          email: m.email,
          role: m.role as any,
          joinedAt: m.created_at.slice(0, 10),
          avatar: m.email.slice(0, 2).toUpperCase(),
        }))
      );
    } catch (err: any) {
      console.error("Failed to load org members:", err);
      setMembers([]);
      setMembersError(err?.message || "Could not load team members.");
    }

    setLoading(false);
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

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail) return;
    try {
      await addSaasOrgMember({ email: inviteEmail, role: inviteRole });
      // No invitation email is sent yet — this only records the member in the
      // workspace. Say exactly that rather than implying a mail went out.
      setInviteFailed(false);
      setInviteStatus(`${inviteEmail} added as ${inviteRole}. No invite email is sent yet — tell them directly.`);
      setInviteEmail("");
      fetchStatus();
    } catch (err: any) {
      console.error("Failed to add org member:", err);
      setInviteFailed(true);
      setInviteStatus(`Couldn't add ${inviteEmail}: ${err?.message || "please try again."}`);
    }
    setTimeout(() => setInviteStatus(null), 6000);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-3">
        <div className="w-6 h-6 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin" />
        <div className="text-xs text-zinc-500 font-semibold font-mono">Loading workspace configuration…</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <div className="text-[10px] font-bold tracking-widest text-emerald-600 uppercase">
          Stage 05 · Master SaaS Controls
        </div>
        <h2 className="text-xl font-bold text-zinc-900 tracking-tight font-sans mt-0.5">
          Workspace Settings & Organization Controls
        </h2>
        <p className="text-xs text-zinc-500 font-medium mt-0.5">
          Manage Amazon connections, team members, RBAC permissions, and audit logs.
        </p>
      </div>

      {/* Tabs Header */}
      <div className="flex items-center gap-1 border-b border-black/5 pb-2">
        {[
          { id: "connections", label: "🔌 Amazon Connections" },
          { id: "teams", label: "👥 Team & RBAC" },
          { id: "usage", label: "📊 Usage" },
          { id: "audit", label: "📋 Audit Logs" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === tab.id
                ? "bg-zinc-900 text-white shadow-sm"
                : "text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: AMAZON CONNECTIONS */}
      {activeTab === "connections" && (
        <div className="space-y-4">
          {connected ? (
            <div className="bg-white border border-black/5 border-l-4 border-l-emerald-500 rounded-2xl p-6 space-y-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-2 py-0.5 rounded uppercase tracking-wider">
                    Connected 🟢
                  </span>
                  <h3 className="text-sm font-bold text-zinc-900 mt-2">Amazon Seller Account Linked</h3>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-zinc-400 font-bold block uppercase">Marketplace</span>
                  <span className="text-xs font-bold text-zinc-700">
                    {MARKETPLACE_NAMES[accounts[0]?.marketplace_id] || accounts[0]?.marketplace_id || "Amazon India"}
                  </span>
                </div>
              </div>

              <div className="border-t border-black/5 pt-4 space-y-2.5">
                {accounts.map((acc, index) => (
                  <div key={index} className="flex justify-between items-center bg-zinc-50 p-3 rounded-xl border border-black/5">
                    <div>
                      <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Selling Partner ID</span>
                      <span className="font-mono text-xs font-bold text-zinc-700">{acc.selling_partner_id}</span>
                    </div>
                    <div className="text-right flex items-center gap-6">
                      <div>
                        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Region</span>
                        <span className="font-mono text-xs font-bold text-zinc-700">{MARKETPLACE_NAMES[acc.marketplace_id] || acc.marketplace_id}</span>
                      </div>
                      <div>
                        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">Linked</span>
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
                  className="text-xs font-bold text-red-500 hover:text-red-600 transition-colors uppercase tracking-wider cursor-pointer disabled:opacity-50"
                >
                  {isPending ? "Disconnecting…" : "Disconnect Amazon account"}
                </button>
              </div>
              {message && <p className="text-xs font-semibold text-zinc-600">{message}</p>}
            </div>
          ) : (
            <div className="bg-white border border-black/5 rounded-2xl p-6 shadow-sm space-y-5">
              <div className="flex items-start gap-4">
                <div className="text-3xl leading-none">🔗</div>
                <div>
                  <h3 className="text-sm font-bold text-zinc-900">Connect Your Amazon Seller Account</h3>
                  <p className="text-xs text-zinc-500 font-medium leading-relaxed mt-1">
                    You&apos;ll be directed to Amazon Seller Central to approve read-only permissions. ScoutVeda never sees your Amazon password.
                  </p>
                </div>
              </div>

              <div className="flex flex-col gap-1 w-full max-w-xs">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Marketplace</label>
                <select
                  value={marketplaceId}
                  onChange={(e) => setMarketplaceId(e.target.value)}
                  className="w-full text-xs font-semibold text-zinc-800 bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                >
                  <option value="A21TJRUUN4KGV">🇮🇳 Amazon India (amazon.in)</option>
                  <option value="ATVPDKIKX0DER">🇺🇸 Amazon USA (amazon.com)</option>
                  <option value="A1F83G8C2ARO7P">🇬🇧 Amazon UK (amazon.co.uk)</option>
                  <option value="A1PA6795UKMFR9">🇩🇪 Amazon Germany (amazon.de)</option>
                  <option value="A13V1IB3VIYZZH">🇫🇷 Amazon France (amazon.fr)</option>
                  <option value="APJ6JRA9NG5V4">🇮🇹 Amazon Italy (amazon.it)</option>
                  <option value="A1RKKUPIHCS9HS">🇪🇸 Amazon Spain (amazon.es)</option>
                  <option value="A2EUQ1WTGCTBG2">🇨🇦 Amazon Canada (amazon.ca)</option>
                  <option value="A39IBJ37TRP1C6">🇦🇺 Amazon Australia (amazon.com.au)</option>
                  <option value="A1VC38T7YXB528">🇯🇵 Amazon Japan (amazon.co.jp)</option>
                  <option value="A1AM78C64UM0Y8">🇲🇽 Amazon Mexico (amazon.com.mx)</option>
                  <option value="A2VIGQ35RCS4UG">🇦🇪 Amazon UAE (amazon.ae)</option>
                </select>
              </div>

              {appConfigured ? (
                <a
                  href={getAuthorizeUrl()}
                  className="btn-primary inline-block w-auto px-6 py-2.5 text-xs font-bold text-center tracking-wide uppercase shadow-sm"
                >
                  🔌 Connect Amazon Account
                </a>
              ) : (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <p className="text-xs font-semibold text-amber-900 leading-relaxed">
                    Amazon self-authorization is running in interim mode for your account. Official public OAuth setup is pending Amazon Developer Support case #21243620901.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: TEAM & RBAC (Blueprint Stage 5) */}
      {activeTab === "teams" && (
        <div className="space-y-6">
          {/* Invite Form */}
          <div className="bg-white border border-black/5 rounded-2xl p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-zinc-900">Invite Team Member</h3>
            <form onSubmit={handleInvite} className="flex flex-col sm:flex-row gap-3">
              <input
                type="email"
                required
                placeholder="colleague@company.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                className="flex-1 text-xs px-3.5 py-2 rounded-xl border border-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              />
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as any)}
                className="text-xs px-3 py-2 rounded-xl border border-zinc-200 bg-zinc-50 font-semibold text-zinc-700"
              >
                <option value="Admin">Admin (Full Ops)</option>
                <option value="Analyst">Analyst (Research)</option>
                <option value="Viewer">Viewer (Read-Only)</option>
              </select>
              <button
                type="submit"
                className="px-5 py-2 bg-emerald-600 text-white rounded-xl text-xs font-bold hover:bg-emerald-700 transition shadow-sm shrink-0"
              >
                Add Member
              </button>
            </form>
            {inviteStatus && (
              <p className={`text-xs font-semibold ${inviteFailed ? "text-red-700" : "text-emerald-700"}`}>
                {inviteStatus}
              </p>
            )}
            <p className="text-[11px] text-zinc-500">
              Adding a member records them in this workspace. Invitation emails are not
              wired up yet, so you will need to let them know yourself.
            </p>
          </div>

          {/* Members Table */}
          <div className="bg-white border border-black/5 rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-zinc-900">
                Organization Members ({members.length})
              </h3>
              <span className="text-[11px] font-semibold text-zinc-500">Workspace: Main Brand</span>
            </div>

            {membersError && (
              <p className="text-xs font-semibold text-red-700 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
                {membersError}
              </p>
            )}

            {!membersError && members.length === 0 && (
              <p className="text-xs text-zinc-500 bg-zinc-50 border border-dashed border-zinc-200 rounded-xl px-4 py-6 text-center">
                No additional team members yet. Add one above to share this workspace.
              </p>
            )}

            <div className="space-y-2">
              {members.map((m) => (
                <div key={m.id} className="flex items-center justify-between p-3 rounded-xl border border-zinc-100 bg-zinc-50/50">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-900 font-bold text-xs flex items-center justify-center border border-emerald-200">
                      {m.avatar}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-zinc-900">{m.name}</div>
                      <div className="text-[11px] text-zinc-500">{m.email}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                      m.role === "Owner" ? "bg-purple-100 text-purple-900" :
                      m.role === "Admin" ? "bg-blue-100 text-blue-900" :
                      m.role === "Analyst" ? "bg-emerald-100 text-emerald-900" : "bg-zinc-200 text-zinc-800"
                    }`}>
                      {m.role}
                    </span>
                    <span className="text-[11px] text-zinc-400 font-mono">{m.joinedAt}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: USAGE
          This was a "Subscription & Billing" tab showing an Active Plan badge,
          "Pro Reseller Plan", "₹2,999/mo", "Renews July 2027" and a Manage
          Billing button. None of it existed -- there is no billing system, no
          plan, and no payment provider wired up, and the button went nowhere.
          The seat/account "limits" were two hardcoded constants, so the
          progress bars were measuring real counts against invented caps.
          What is left below is only what can actually be counted. */}
      {activeTab === "usage" && (
        <div className="space-y-6">
          <div className="bg-white border border-black/5 rounded-2xl p-6 shadow-sm space-y-6">
            <div className="border-b border-zinc-100 pb-4">
              <h3 className="text-lg font-extrabold text-zinc-900">Usage</h3>
              <p className="text-xs text-zinc-500 font-medium mt-1">
                Current totals for this workspace. ScoutVeda has no subscription or
                billing set up, so there are no plan limits to measure against.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-zinc-50 border border-zinc-200/80">
                <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Connected Storefronts</div>
                <div className="text-lg font-bold text-zinc-900 mt-1">
                  {accounts.length} {accounts.length === 1 ? "account" : "accounts"}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-zinc-50 border border-zinc-200/80">
                <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Team Members</div>
                <div className="text-lg font-bold text-zinc-900 mt-1">
                  {members.length} {members.length === 1 ? "member" : "members"}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-zinc-50 border border-zinc-200/80">
                <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">ASIN Validations</div>
                <div className="text-lg font-bold text-zinc-900 mt-1">No cap</div>
                <div className="text-[11px] text-zinc-500 mt-1">Not metered or limited</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: AUDIT LOGS (Blueprint Stage 5 & Section 10) */}
      {activeTab === "audit" && (
        <div className="bg-white border border-black/5 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-zinc-900">Compliance & Security Audit Log</h3>
              <p className="text-xs text-zinc-500">Immutable record of sensitive workspace actions, credential changes, and role assignments.</p>
            </div>
            <span className="text-[10px] font-mono bg-zinc-100 text-zinc-700 px-2.5 py-1 rounded-md font-bold">
              {auditLogs.length} {auditLogs.length === 1 ? "Log" : "Logs"} Recorded
            </span>
          </div>

          {auditError && (
            <p className="text-xs font-semibold text-red-700 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
              {auditError}
            </p>
          )}

          {!auditError && auditLogs.length === 0 && (
            <p className="text-xs text-zinc-500 bg-zinc-50 border border-dashed border-zinc-200 rounded-xl px-4 py-6 text-center">
              No audit events recorded yet. Sensitive actions will appear here as they happen.
            </p>
          )}

          <div className="space-y-2">
            {auditLogs.map((log) => (
              <div key={log.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-xl border border-zinc-100 bg-zinc-50/50 text-xs">
                <div className="space-y-0.5">
                  <div className="font-bold text-zinc-900">{log.action}</div>
                  <div className="text-[11px] text-zinc-500 font-mono">Target: {log.target}</div>
                </div>
                <div className="text-left sm:text-right mt-2 sm:mt-0 font-mono text-[11px] text-zinc-400 space-y-0.5">
                  <div>Actor: <strong className="text-zinc-700">{log.actor}</strong></div>
                  <div>{log.timestamp} · {log.ip}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
