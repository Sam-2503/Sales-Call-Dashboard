import { Link, NavLink, Outlet } from "react-router-dom";

import { copy } from "@/copy";
import { useTheme } from "@/theme/useTheme";

import { AppBanners } from "./AppBanners";

function navClass({ isActive }: { isActive: boolean }): string {
  return [
    "inline-flex min-h-11 items-center rounded-control px-2.5 text-sm font-bold",
    "focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-focus",
    isActive ? "bg-wash text-ink" : "text-muted hover:text-ink",
  ].join(" ");
}

export function AppShell() {
  useTheme();

  return (
    <div className="flex min-h-dvh flex-col bg-paper text-ink">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-control focus:border focus:border-hairline focus:bg-surface focus:px-4 focus:py-3 focus:font-bold"
      >
        {copy.common.skipToContent}
      </a>

      <header className="border-b border-hairline">
        <div className="mx-auto flex max-w-[760px] flex-wrap items-center justify-between gap-2 px-4 py-2">
          <Link to="/" className="text-[19px] font-bold tracking-tight no-underline">
            {copy.appName}
          </Link>
          <nav aria-label={copy.nav.main} className="flex flex-wrap items-center gap-1">
            <NavLink to="/calls" className={navClass}>
              {copy.nav.calls}
            </NavLink>
            <NavLink to="/progress" className={navClass}>
              {copy.nav.progress}
            </NavLink>
            <NavLink to="/settings" className={navClass}>
              {copy.nav.settings}
            </NavLink>
          </nav>
        </div>
      </header>

      <AppBanners />

      <main id="main" className="mx-auto w-full max-w-[760px] flex-1 px-4 py-10">
        <Outlet />
      </main>

      <footer className="border-t border-hairline">
        <div className="mx-auto flex max-w-[760px] flex-wrap items-center justify-between gap-2 px-4 py-5 text-sm text-muted">
          <span>{copy.appName}</span>
          <Link to="/how-it-works" className="font-bold text-ink">
            {copy.shell.footer}
          </Link>
        </div>
      </footer>
    </div>
  );
}
