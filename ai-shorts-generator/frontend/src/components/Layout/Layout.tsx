import { Outlet, NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Wand2,
  Layers,
  ListVideo,
  Settings,
  Zap,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useAppStore } from '@/store';
import { useRenderSocket } from '@/hooks/useRenderSocket';
import RenderQueueBar from '@components/RenderQueueBar/RenderQueueBar';
import clsx from 'clsx';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/generator', label: 'Generator', icon: Wand2 },
  { path: '/templates', label: 'Templates', icon: Layers },
  { path: '/batch', label: 'Batch', icon: ListVideo },
  { path: '/settings', label: 'Settings', icon: Settings },
] as const;

export default function Layout() {
  useRenderSocket();
  const { sidebarOpen, toggleSidebar } = useAppStore();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* ── Sidebar ──────────────────────────── */}
      <motion.aside
        animate={{ width: sidebarOpen ? 220 : 64 }}
        transition={{ duration: 0.25, ease: 'easeInOut' }}
        className="relative flex flex-col bg-background-secondary border-r border-border shrink-0 overflow-hidden"
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-border">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-purple to-neon-blue flex items-center justify-center shrink-0">
            <Zap className="w-4 h-4 text-white" />
          </div>
          {sidebarOpen && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="font-display font-bold text-sm gradient-text whitespace-nowrap"
            >
              AI Shorts
            </motion.span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex flex-col gap-1 p-2 flex-1">
          {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-neon-purple/15 text-neon-purple border border-neon-purple/25'
                    : 'text-text-secondary hover:text-text-primary hover:bg-background-hover'
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {sidebarOpen && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="whitespace-nowrap"
                >
                  {label}
                </motion.span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Toggle button */}
        <button
          onClick={toggleSidebar}
          className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-background-card border border-border flex items-center justify-center hover:border-neon-purple transition-colors z-10"
        >
          {sidebarOpen ? (
            <ChevronLeft className="w-3 h-3 text-text-secondary" />
          ) : (
            <ChevronRight className="w-3 h-3 text-text-secondary" />
          )}
        </button>
      </motion.aside>

      {/* ── Main ─────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <main className="flex-1 overflow-y-auto p-6">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
            className="h-full"
          >
            <Outlet />
          </motion.div>
        </main>
        <RenderQueueBar />
      </div>
    </div>
  );
}
