'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useDashboardStore } from '@/stores/dashboard';

const navItems = [
  { href: '/', label: 'Robot Registry', icon: 'R' },
  { href: '/runtime', label: 'Runtime', icon: 'RT' },
  { href: '/providers', label: 'Providers', icon: 'P' },
  { href: '/events', label: 'Event Bus', icon: 'EV' },
  { href: '/episodes', label: 'Episodes', icon: 'EP' },
  { href: '/missions', label: 'Missions', icon: 'M' },
  { href: '/skills', label: 'Skills', icon: 'S' },
  { href: '/mcap', label: 'MCAP Replay', icon: 'MP' },
  { href: '/memory', label: 'Memory', icon: 'Me' },
  { href: '/safety', label: 'Safety', icon: 'Sa' },
  { href: '/embodiment', label: 'Embodiment', icon: 'E' },
];

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const { sidebarOpen, setSidebarOpen } = useDashboardStore();
  const pathname = usePathname();

  return (
    <div className="flex h-screen bg-slate-50">
      <aside
        className={`${
          sidebarOpen ? 'w-56' : 'w-14'
        } flex-shrink-0 bg-slate-900 text-white transition-all duration-200 flex flex-col`}
      >
        <div className="h-14 flex items-center px-4 border-b border-slate-700">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-slate-400 hover:text-white text-sm font-bold"
          >
            {sidebarOpen ? 'ROSClaw' : 'R'}
          </button>
        </div>
        <nav className="flex-1 py-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center px-4 py-2.5 text-sm transition-colors ${
                pathname === item.href
                  ? 'bg-rosclaw-700 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <span className="w-6 text-center font-bold text-xs">{item.icon}</span>
              {sidebarOpen && <span className="ml-2">{item.label}</span>}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-700 text-xs text-slate-500">
          {sidebarOpen && <span>v0.1.0 MVP</span>}
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <div className="h-14 bg-white border-b border-slate-200 flex items-center px-6">
          <h1 className="text-lg font-semibold text-slate-800">
            {navItems.find((i) => i.href === pathname)?.label || 'ROSClaw Dashboard'}
          </h1>
        </div>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
