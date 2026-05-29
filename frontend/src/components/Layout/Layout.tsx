import { Outlet, NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  RiDashboard3Line,
  RiVideoLine,
  RiImage2Line,
  RiLayoutMasonryLine,
  RiListCheck3,
  RiSettings4Line,
  RiFlashlightLine,
  RiArrowLeftSLine,
  RiArrowRightSLine,
} from 'react-icons/ri';
import { useAppStore } from '@/store';
import { useRenderSocket } from '@/hooks/useRenderSocket';
import RenderQueueBar from '@components/RenderQueueBar/RenderQueueBar';
import clsx from 'clsx';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: RiDashboard3Line },
  { path: '/generator', label: 'Generator', icon: RiVideoLine },
  { path: '/imager', label: 'Imager', icon: RiImage2Line },
  { path: '/templates', label: 'Templates', icon: RiLayoutMasonryLine },
  { path: '/batch', label: 'Batch', icon: RiListCheck3 },
  { path: '/settings', label: 'Settings', icon: RiSettings4Line },
] as const;

export default function Layout() {
  useRenderSocket();
  const { sidebarOpen, toggleSidebar } = useAppStore();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <motion.aside
        animate={{ width: sidebarOpen ? 212 : 56 }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        className="relative flex flex-col bg-background-secondary border-r border-border shrink-0 overflow-hidden"
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-3.5 py-4 border-b border-border">
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center shrink-0">
            <RiFlashlightLine className="w-4 h-4 text-white" />
          </div>
          {sidebarOpen && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-semibold text-sm text-text-primary whitespace-nowrap tracking-tight"
            >
              AI Shorts
            </motion.span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex flex-col gap-0.5 p-2 flex-1">
          {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-accent/10 text-accent'
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

        {/* Toggle */}
        <button
          onClick={toggleSidebar}
          className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-background-card border border-border flex items-center justify-center hover:border-accent transition-colors z-10"
        >
          {sidebarOpen
            ? <RiArrowLeftSLine className="w-3.5 h-3.5 text-text-secondary" />
            : <RiArrowRightSLine className="w-3.5 h-3.5 text-text-secondary" />
          }
        </button>
      </motion.aside>

      {/* Main */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <main className="flex-1 overflow-y-auto p-6">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
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
