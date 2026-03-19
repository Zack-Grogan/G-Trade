"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { SignInButton, UserButton, useUser } from "@clerk/nextjs";
import { useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";

type NavItem = {
  href: string;
  label: string;
  description: string;
};

type NavSection = {
  label: string;
  items: NavItem[];
};

const NAV_SECTIONS: NavSection[] = [
  {
    label: "Operations",
    items: [
      { href: "/", label: "Dashboard", description: "Live pulse" },
      { href: "/chart", label: "Chart", description: "Market view" },
      { href: "/runs", label: "Runs", description: "Run index" },
    ],
  },
  {
    label: "Analysis",
    items: [
      { href: "/accounts", label: "Accounts", description: "Ledger" },
      { href: "/advisory", label: "Advisory", description: "RLM and reports" },
    ],
  },
  {
    label: "Infrastructure",
    items: [{ href: "/system", label: "System", description: "Health" }],
  },
];

const NAV_ITEMS = NAV_SECTIONS.flatMap((section) => section.items);

function isActivePath(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function LoginScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 py-16 text-zinc-100">
      <div className="w-full max-w-md rounded-xl border border-zinc-800/80 bg-zinc-950 p-8">
        <p className="text-[11px] uppercase tracking-[0.24em] text-cyan-300">G-Trade operator console</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-zinc-50">Sign in to view the account ledger and advisory tools</h1>
        <p className="mt-4 text-sm leading-6 text-zinc-400">
          This console stays read-only. Execution stays on the Mac, and the cloud surfaces remain hidden until you authenticate.
        </p>
        <div className="mt-6">
          <SignInButton mode="modal">
            <span className="inline-flex w-full cursor-pointer items-center justify-center rounded-md border border-cyan-500/30 bg-cyan-500/15 px-4 py-3 text-sm font-medium text-cyan-100 transition hover:bg-cyan-500/20">
              Sign in to continue
            </span>
          </SignInButton>
        </div>
      </div>
    </div>
  );
}

export function AppShell({
  children,
}: {
  children: ReactNode;
}) {
  const { isLoaded, isSignedIn } = useUser();
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const sidebarStorageKey = "g-trade.sidebar-collapsed";
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window === "undefined") {
      return true;
    }

    const stored = window.localStorage.getItem(sidebarStorageKey);
    return stored === "0" ? false : true;
  });
  const [query, setQuery] = useState("");
  const searchRef = useRef<HTMLInputElement | null>(null);

  const activeItem = useMemo(() => NAV_ITEMS.find((item) => isActivePath(pathname, item.href)) ?? NAV_ITEMS[0], [pathname]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const isMacShortcut = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";
      if (!isMacShortcut) {
        return;
      }

      event.preventDefault();
      searchRef.current?.focus();
      searchRef.current?.select();
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(sidebarStorageKey, sidebarCollapsed ? "1" : "0");
  }, [sidebarCollapsed]);

  if (!isLoaded) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 py-16 text-zinc-100">
        <div className="rounded-xl border border-zinc-800/80 bg-zinc-950 px-6 py-4 text-sm text-zinc-400">
          Loading operator console
        </div>
      </div>
    );
  }

  if (!isSignedIn) {
    return <LoginScreen />;
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleaned = query.trim();
    router.push(cleaned ? `/?q=${encodeURIComponent(cleaned)}` : "/");
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="flex min-h-screen">
        <aside
          className={`fixed inset-y-0 left-0 z-40 w-[18rem] border-r border-zinc-800/80 bg-zinc-950 transition-[transform,width] duration-200 lg:translate-x-0 ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          } ${sidebarCollapsed ? "lg:w-16" : "lg:w-[18rem]"} lg:static lg:flex lg:flex-col`}
        >
          <div className="flex h-full flex-col">
            <div className={`border-b border-zinc-800/80 px-5 py-5 ${sidebarCollapsed ? "lg:px-3" : ""}`}>
              <Link href="/" className={`inline-flex items-center gap-3 ${sidebarCollapsed ? "lg:w-full lg:justify-center" : ""}`}>
                <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950 text-sm font-semibold text-cyan-300">
                  GT
                </span>
                <div className={sidebarCollapsed ? "lg:hidden" : ""}>
                  <p className="text-xs uppercase tracking-[0.24em] text-zinc-500">G-Trade</p>
                  <p className="text-sm font-medium text-zinc-100">Operator console</p>
                </div>
              </Link>
            </div>

            <div className={`flex-1 overflow-y-auto px-4 py-5 ${sidebarCollapsed ? "lg:px-2" : ""}`}>
              <div className="space-y-5">
                {NAV_SECTIONS.map((section, sectionIndex) => (
                  <div key={section.label} className={sectionIndex > 0 ? "border-t border-zinc-800/80 pt-5" : ""}>
                    <p className={`px-2 text-[10px] uppercase tracking-[0.24em] text-zinc-500 ${sidebarCollapsed ? "lg:hidden" : ""}`}>{section.label}</p>
                    <div className="mt-3 space-y-1">
                      {section.items.map((item) => {
                        const active = isActivePath(pathname, item.href);
                        return (
                          <Link
                            key={item.href}
                            href={item.href}
                            onClick={() => setSidebarOpen(false)}
                            title={sidebarCollapsed ? item.label : undefined}
                            className={`flex items-center justify-between rounded-lg border px-3 py-3 transition ${
                              sidebarCollapsed ? "lg:justify-center lg:px-2" : ""
                            } ${
                              active
                                ? "border-cyan-500/30 bg-cyan-500/10 text-zinc-50"
                                : "border-transparent text-zinc-400 hover:border-zinc-800 hover:bg-zinc-900 hover:text-zinc-100"
                            }`}
                          >
                            <span className={`min-w-0 ${sidebarCollapsed ? "lg:hidden" : ""}`}>
                              <span className="block text-sm font-medium">{item.label}</span>
                              <span className="block text-xs text-zinc-500">{item.description}</span>
                            </span>
                            <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-zinc-800 bg-zinc-950 text-[11px] font-semibold uppercase tracking-[0.2em] text-zinc-300 ${sidebarCollapsed ? "" : "lg:hidden"}`}>
                              {item.label.slice(0, 2)}
                            </span>
                            <span className={`h-2 w-2 rounded-full ${active ? "bg-cyan-400" : "bg-zinc-700"} ${sidebarCollapsed ? "lg:hidden" : ""}`} />
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </aside>

        {sidebarOpen ? <button type="button" aria-label="Close navigation drawer" onClick={() => setSidebarOpen(false)} className="fixed inset-0 z-30 bg-black/50 lg:hidden" /> : null}

        <div className="flex min-w-0 flex-1 flex-col lg:ml-0">
          <header className="sticky top-0 z-20 border-b border-zinc-800/80 bg-zinc-950">
            <div className="flex items-center gap-4 px-4 py-3 sm:px-6 lg:px-8">
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="inline-flex items-center justify-center rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 transition hover:border-zinc-700 hover:bg-zinc-900 lg:hidden"
                aria-label="Open navigation drawer"
              >
                Menu
              </button>

              <button
                type="button"
                onClick={() => setSidebarCollapsed((current) => !current)}
                aria-pressed={sidebarCollapsed}
                className="hidden items-center justify-center rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 transition hover:border-zinc-700 hover:bg-zinc-900 lg:inline-flex"
              >
                {sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              </button>

              <div className="min-w-0 flex-1">
                <p className="truncate text-xs uppercase tracking-[0.22em] text-zinc-500">{activeItem.label}</p>
                <p className="truncate text-sm text-zinc-300">{activeItem.description}</p>
              </div>

              <form onSubmit={submitSearch} className="hidden flex-1 max-w-xl items-center gap-3 md:flex">
                <div className="relative flex-1">
                  <input
                    ref={searchRef}
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search runs, reports, accounts…"
                    className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-4 py-2.5 pr-20 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-cyan-500/30 focus:ring-2 focus:ring-cyan-500/10"
                  />
                  <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded-lg border border-zinc-800 bg-zinc-950 px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-zinc-500">
                    ⌘K
                  </span>
                </div>
              </form>

              <div className="ml-auto flex items-center gap-3">
                <div className="hidden rounded-md border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-400 md:block">
                  Clerk-authenticated
                </div>
                <UserButton />
              </div>
            </div>
          </header>

          <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
            <div className="mx-auto w-full max-w-[1440px]">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}
