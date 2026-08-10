"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState, useTransition } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { logout } from "@/lib/auth-actions";
import { setMarketplacePreference } from "@/lib/marketplace-actions";

type SidebarItem = {
  href: string;
  label: string;
  icon: React.ReactNode;
  disabled?: boolean;
};

type SidebarSection = {
  title: string;
  items: SidebarItem[];
};

// Dashboard tabs that have their own sidebar entry. While one of these is the
// active tab, the plain "Dashboard" entry should not also claim the highlight.
const TAB_OWNED_BY_ITEM = ["storefront"];

export default function Sidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [open, setOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [selectedMarketplace, setSelectedMarketplace] = useState("amazon.in");
  const [sellerTag, setSellerTag] = useState("Private Label");
  const [isPending, startTransition] = useTransition();
  const accountMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem("selectedMarketplace") || "amazon.in";
    setSelectedMarketplace(stored);

    const loadConfig = () => {
      const savedConfig = localStorage.getItem("scoutveda_seller_config");
      if (savedConfig) {
        try {
          const cfg = JSON.parse(savedConfig);
          const typeLabels: Record<string, string> = {
            private_label: "Private Label",
            wholesale: "Wholesale",
            arbitrage: "Arbitrage",
            agency: "Agency",
            brand_owner: "Brand Owner",
          };
          setSellerTag(typeLabels[cfg.sellerType] || "Private Label");
        } catch (e) {}
      }
    };
    loadConfig();

    const handleConfigUpdate = () => loadConfig();
    window.addEventListener("scoutveda_config_updated", handleConfigUpdate);
    return () => window.removeEventListener("scoutveda_config_updated", handleConfigUpdate);
  }, []);

  const handleMarketplaceChange = (val: string) => {
    setSelectedMarketplace(val);
    localStorage.setItem("selectedMarketplace", val);
    
    startTransition(() => {
      setMarketplacePreference(val);
    });
    
    window.dispatchEvent(new Event("marketplaceChanged"));
  };

  // close the mobile drawer and the account menu on route change
  useEffect(() => {
    setOpen(false);
    setAccountOpen(false);
  }, [pathname]);

  // dismiss the account menu on an outside click or Escape
  useEffect(() => {
    if (!accountOpen) return;

    const handlePointerDown = (e: MouseEvent) => {
      if (!accountMenuRef.current?.contains(e.target as Node)) setAccountOpen(false);
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setAccountOpen(false);
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [accountOpen]);

  const sections: SidebarSection[] = [
    {
      title: "Overview",
      items: [
        {
          href: "/dashboard",
          label: "Dashboard",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2v-4zM14 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2v-4z" />
            </svg>
          ),
        },
        {
          href: "/dashboard?tab=storefront",
          label: "Storefront Performance",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
          ),
        },
        {
          href: "/dashboard/alerts",
          label: "Activity / Alerts",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          ),
        },
      ],
    },
    {
      title: "Research",
      items: [
        {
          href: "/dashboard/validator",
          label: "Product Opportunity Finder",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="6" />
              <circle cx="12" cy="12" r="2" />
            </svg>
          ),
        },
        {
          href: "/dashboard/product-database",
          label: "Product Database",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          ),
        },
        {
          href: "/dashboard/competitor-analysis",
          label: "Competitor Analysis",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
            </svg>
          ),
        },
        {
          href: "/dashboard/keywords",
          label: "Keyword Research",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m-3.414-1.414A2 2 0 1119 4a2 2 0 01-4.243 2.828M15 7l-3 3M9 13l-4 4v3h3l4-4M9 13L15 7" />
            </svg>
          ),
        },
        {
          href: "/dashboard/watchlist",
          label: "Trend Explorer",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          ),
        },
      ],
    },
    {
      title: "Catalog & Listings",
      items: [
        {
          href: "/dashboard/my-products",
          label: "My Products",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          ),
        },
        {
          href: "/dashboard/listing",
          label: "Listing Optimizer",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          ),
        },
        {
          href: "/dashboard/listing-health",
          label: "Listing Health",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          ),
        },
      ],
    },
    {
      title: "Operations",
      items: [
        {
          href: "/dashboard/inventory",
          label: "Inventory",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          ),
        },
        {
          href: "/dashboard/profit-calculator",
          label: "Profit & Fees",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <rect x="4" y="4" width="16" height="16" rx="2" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 9h6M9 13h6M9 17h6" />
            </svg>
          ),
        },
        {
          href: "/dashboard/analytics",
          label: "Analytics",
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l4-3v16M9 19l-4-2V4l4 2M9 19l4-3M13 3l6 3v13l-6-3" />
            </svg>
          ),
        },
      ],
    },
  ];

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden sticky top-0 z-30 flex items-center justify-between px-4 py-3 border-b border-black/5 bg-white">
        <div className="flex items-center gap-2">
          <span className="text-xl">🔭</span>
          <span className="font-bold tracking-tight text-zinc-900">ScoutVeda</span>
        </div>
        <button
          onClick={() => setOpen(true)}
          aria-label="Open menu"
          className="text-xl leading-none px-1 text-zinc-700"
        >
          ☰
        </button>
      </div>

      {/* Mobile backdrop */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
            className="md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          />
        )}
      </AnimatePresence>

      <aside
        className={`
          w-64 shrink-0 flex flex-col border-r border-black/5 px-4 py-6
          fixed inset-y-0 left-0 z-50 bg-white
          transition-transform duration-200 ease-out
          ${open ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0 md:sticky md:top-0 md:h-screen md:bg-white md:z-10
        `}
      >
        {/* Brand Area */}
        <div className="mb-6 px-2">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-tight text-zinc-900">
              🔭 ScoutVeda
            </span>
          </div>
          <div className="flex items-center justify-between mt-2">
            <p className="text-[10px] text-zinc-400 leading-relaxed font-semibold uppercase tracking-wider">
              KNK ENTERPRISES
            </p>
            <span className="text-[9px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200/80 px-2 py-0.5 rounded-full">
              {sellerTag}
            </span>
          </div>
        </div>

        {/* Navigation Area */}
        <nav className="flex-1 flex flex-col gap-5 overflow-y-auto pr-1">
          {sections.map((section) => (
            <div key={section.title} className="space-y-1">
              <h3 className="text-[9px] font-bold uppercase tracking-widest text-zinc-500 px-2.5">
                {section.title}
              </h3>
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  // Items like "/dashboard?tab=storefront" carry a query string,
                  // which `pathname` never includes -- comparing the raw href
                  // meant those entries could never light up, and "Dashboard"
                  // stayed highlighted instead. Compare both halves.
                  const [itemPath, itemQuery] = item.href.split("?");
                  const activeTab = searchParams.get("tab") ?? "";
                  const active =
                    pathname === itemPath &&
                    (itemQuery
                      ? itemQuery === `tab=${activeTab}`
                      : !TAB_OWNED_BY_ITEM.includes(activeTab));
                  if (item.disabled) {
                    return (
                      <div
                        key={item.label}
                        className="flex items-center gap-2.5 px-2.5 py-1.5 text-xs text-zinc-600 font-medium cursor-not-allowed"
                      >
                        <span className="shrink-0">{item.icon}</span>
                        <span className="flex-1">{item.label}</span>
                      </div>
                    );
                  }

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className="relative block py-1.5 px-2.5 rounded-lg hover:bg-zinc-100 transition-colors group"
                    >
                      {active && (
                        <motion.div
                          layoutId="nav-active-pill"
                          className="absolute inset-0 rounded-lg bg-zinc-100 border border-black/5"
                          transition={{ type: "spring", stiffness: 450, damping: 38 }}
                        />
                      )}
                      <span
                        className={`relative z-10 flex items-center gap-2.5 text-xs font-semibold transition-colors ${
                          active ? "text-zinc-900 font-bold" : "text-zinc-500 hover:text-zinc-900"
                        }`}
                      >
                        <span className={`shrink-0 transition-opacity ${active ? "opacity-100" : "opacity-60 group-hover:opacity-100"}`}>
                          {item.icon}
                        </span>
                        {item.label}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer / Account / Marketplace selector */}
        <div className="mt-auto pt-3 border-t border-black/5 flex flex-col gap-2">
          {/* Marketplace Selector -- the flag and currency label the control, so
              it carries no separate heading; the footer is tight on space. */}
          <div className="px-2">
            <select
              aria-label="Active marketplace"
              value={selectedMarketplace}
              onChange={(e) => handleMarketplaceChange(e.target.value)}
              className="w-full text-xs font-semibold text-zinc-700 bg-zinc-50 border border-black/10 rounded px-2 py-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus:border-zinc-300 cursor-pointer"
            >
              <option value="amazon.in">🇮🇳 Amazon.in (₹ INR)</option>
              <option value="amazon.com">🇺🇸 Amazon.com ($ USD)</option>
              <option value="amazon.co.uk">🇬🇧 Amazon.co.uk (£ GBP)</option>
              <option value="amazon.de">🇩🇪 Amazon.de (€ EUR)</option>
              <option value="amazon.fr">🇫🇷 Amazon.fr (€ EUR)</option>
              <option value="amazon.it">🇮🇹 Amazon.it (€ EUR)</option>
              <option value="amazon.es">🇪🇸 Amazon.es (€ EUR)</option>
              <option value="amazon.ca">🇨🇦 Amazon.ca ($ CAD)</option>
              <option value="amazon.com.au">🇦🇺 Amazon.com.au ($ AUD)</option>
              <option value="amazon.co.jp">🇯🇵 Amazon.co.jp (¥ JPY)</option>
              <option value="amazon.com.mx">🇲🇽 Amazon.com.mx ($ MXN)</option>
              <option value="amazon.ae">🇦🇪 Amazon.ae (AED)</option>
            </select>
          </div>

          {/* Account menu -- Setup Wizard, Settings, Feedback and Sign Out used
              to sit as four permanently stacked rows, which crowded the footer.
              They live behind one trigger now. */}
          <div ref={accountMenuRef} className="relative px-2">
            {accountOpen && (
              <div
                role="menu"
                className="absolute bottom-full left-2 right-2 mb-1 flex flex-col gap-0.5 rounded-lg border border-black/10 bg-white p-1 text-xs font-medium text-zinc-600 shadow-lg"
              >
                <button
                  role="menuitem"
                  onClick={() => {
                    setAccountOpen(false);
                    window.dispatchEvent(new Event("scoutveda_trigger_setup"));
                  }}
                  className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left transition-colors cursor-pointer hover:bg-emerald-50/60 hover:text-emerald-700 focus-visible:ring-2 focus-visible:ring-zinc-400 focus:outline-none"
                >
                  <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Setup Wizard
                </button>

                <Link
                  role="menuitem"
                  href="/dashboard/settings"
                  onClick={() => setAccountOpen(false)}
                  className="flex items-center gap-2 rounded px-2 py-1.5 transition-colors hover:bg-zinc-50 hover:text-zinc-900 focus-visible:ring-2 focus-visible:ring-zinc-400 focus:outline-none"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Amazon Connection &amp; Settings
                </Link>

                <a
                  role="menuitem"
                  href="mailto:rameshknk143@gmail.com?subject=ScoutVeda Dashboard Feedback"
                  onClick={() => setAccountOpen(false)}
                  className="flex items-center gap-2 rounded px-2 py-1.5 transition-colors hover:bg-zinc-50 hover:text-zinc-900 focus-visible:ring-2 focus-visible:ring-zinc-400 focus:outline-none"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Send Feedback
                </a>

                <button
                  role="menuitem"
                  onClick={() => logout()}
                  className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left transition-colors cursor-pointer hover:bg-red-50 hover:text-red-600 focus-visible:ring-2 focus-visible:ring-zinc-400 focus:outline-none"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Sign Out
                </button>
              </div>
            )}

            <button
              onClick={() => setAccountOpen((v) => !v)}
              aria-haspopup="menu"
              aria-expanded={accountOpen}
              className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs font-semibold text-zinc-600 transition-colors cursor-pointer hover:bg-zinc-100 hover:text-zinc-900 focus-visible:ring-2 focus-visible:ring-zinc-400 focus:outline-none"
            >
              <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <circle cx="12" cy="8" r="3.25" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 20a7.5 7.5 0 0115 0" />
              </svg>
              <span className="flex-1 text-left">Account</span>
              <svg
                className={`w-3 h-3 shrink-0 transition-transform ${accountOpen ? "" : "rotate-180"}`}
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 15l-6-6-6 6" />
              </svg>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
