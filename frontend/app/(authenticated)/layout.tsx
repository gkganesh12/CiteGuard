"use client";

import { UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ListChecks,
  FileText,
  Users,
  Key,
  Settings,
  CreditCard,
  Shield,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/queue", label: "Review Queue", icon: ListChecks },
  { href: "/audit", label: "Audit Exports", icon: FileText },
  { href: "/firm/users", label: "Team", icon: Users },
  { href: "/firm/api-keys", label: "API Keys", icon: Key },
  { href: "/firm/settings", label: "Settings", icon: Settings },
  { href: "/firm/billing", label: "Billing", icon: CreditCard },
];

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside
        className={`${
          collapsed ? "w-16" : "w-56"
        } fixed inset-y-0 left-0 z-30 flex flex-col border-r border-gray-200 bg-white transition-all duration-200`}
      >
        {/* Logo */}
        <div className="flex h-14 items-center px-4">
          {!collapsed ? (
            <Link href="/dashboard" className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gray-900">
                <Shield className="h-4 w-4 text-white" />
              </div>
              <span className="text-sm font-semibold tracking-tight">
                CiteGuard
              </span>
            </Link>
          ) : (
            <Link href="/dashboard" className="mx-auto">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gray-900">
                <Shield className="h-4 w-4 text-white" />
              </div>
            </Link>
          )}
        </div>

        {/* Nav */}
        <nav className="mt-1 flex-1 space-y-0.5 px-3">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium transition-colors ${
                  isActive
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                } ${collapsed ? "justify-center px-2" : ""}`}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Shortcuts */}
        {!collapsed && (
          <div className="mx-3 mb-3 rounded-md bg-gray-50 p-2.5">
            <p className="text-[10px] font-medium uppercase tracking-wide text-gray-400">
              Shortcuts
            </p>
            <div className="mt-1.5 grid grid-cols-2 gap-x-1 gap-y-1 text-[11px] text-gray-500">
              <span><span className="kbd">A</span> Approve</span>
              <span><span className="kbd">O</span> Override</span>
              <span><span className="kbd">R</span> Reject</span>
              <span><span className="kbd">D</span> Defer</span>
              <span><span className="kbd">J</span>/<span className="kbd">K</span> Nav</span>
              <span><span className="kbd">?</span> Help</span>
            </div>
          </div>
        )}

        {/* Collapse toggle */}
        <div className="border-t border-gray-200 p-3">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex w-full items-center justify-center rounded-md p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
          >
            {collapsed ? (
              <PanelLeftOpen className="h-4 w-4" />
            ) : (
              <PanelLeftClose className="h-4 w-4" />
            )}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div
        className={`flex flex-1 flex-col ${
          collapsed ? "ml-16" : "ml-56"
        } transition-all duration-200`}
      >
        {/* Top bar */}
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-gray-200 bg-white/80 px-6 backdrop-blur-sm">
          <h2 className="text-sm font-medium text-gray-500">
            {navItems.find((i) => pathname.startsWith(i.href))?.label || "CiteGuard"}
          </h2>
          <UserButton />
        </header>

        {/* Page */}
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
