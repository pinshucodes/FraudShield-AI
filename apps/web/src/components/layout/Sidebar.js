'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  LayoutDashboard,
  ArrowLeftRight,
  ShieldAlert,
  Brain,
  Settings,
  Users,
  FileText,
  Activity,
  ChevronLeft,
  ChevronRight,
  Shield,
  Bell,
  LogOut,
} from 'lucide-react';
import styles from './Sidebar.module.css';

const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { label: 'Transactions', icon: ArrowLeftRight, href: '/dashboard/transactions' },
  { label: 'Risk Engine', icon: ShieldAlert, href: '/dashboard/risk' },
  { label: 'ML Models', icon: Brain, href: '/dashboard/models' },
  { label: 'Alerts', icon: Bell, href: '/dashboard/alerts', badge: 5 },
  { label: 'Users', icon: Users, href: '/dashboard/users' },
  { label: 'Reports', icon: FileText, href: '/dashboard/reports' },
  { label: 'System', icon: Activity, href: '/dashboard/system' },
];

const BOTTOM_ITEMS = [
  { label: 'Settings', icon: Settings, href: '/dashboard/settings' },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <aside className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}>
      {/* Logo */}
      <div className={styles.logo}>
        <div className={styles.logoIcon}>
          <Shield size={24} />
        </div>
        {!collapsed && (
          <div className={styles.logoText}>
            <span className={styles.logoTitle}>FraudShield</span>
            <span className={styles.logoSubtitle}>AI</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className={styles.nav}>
        <ul className={styles.navList}>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || 
              (item.href !== '/dashboard' && pathname?.startsWith(item.href));
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`${styles.navItem} ${isActive ? styles.active : ''}`}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon size={20} />
                  {!collapsed && <span>{item.label}</span>}
                  {!collapsed && item.badge && (
                    <span className={styles.badge}>{item.badge}</span>
                  )}
                  {isActive && <div className={styles.activeIndicator} />}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Bottom section */}
      <div className={styles.bottom}>
        {BOTTOM_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={styles.navItem}
              title={collapsed ? item.label : undefined}
            >
              <Icon size={20} />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}

        {/* Collapse toggle */}
        <button
          className={styles.collapseBtn}
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          {!collapsed && <span>Collapse</span>}
        </button>

        {/* Logout */}
        <button
          className={styles.navItem}
          onClick={logout}
          title={collapsed ? 'Logout' : undefined}
          style={{ background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left', color: 'inherit' }}
        >
          <LogOut size={20} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
