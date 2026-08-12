'use client';

import { ArrowLeftRight, ShieldAlert, Activity, Gauge } from 'lucide-react';
import StatCard from '@/components/dashboard/StatCard';
import TransactionChart from '@/components/dashboard/TransactionChart';
import AlertFeed from '@/components/dashboard/AlertFeed';
import RecentTransactions from '@/components/dashboard/RecentTransactions';
import RiskDistribution from '@/components/dashboard/RiskDistribution';
import styles from './page.module.css';

const STATS = [
  {
    icon: ArrowLeftRight,
    label: 'Total Transactions',
    value: '2,847,391',
    change: '12.5%',
    changeType: 'positive',
    accentColor: '#3B82F6',
  },
  {
    icon: ShieldAlert,
    label: 'Fraud Detected',
    value: '1,847',
    change: '3.2%',
    changeType: 'negative',
    accentColor: '#EF4444',
  },
  {
    icon: Gauge,
    label: 'Avg Risk Score',
    value: '23.4',
    change: '1.8%',
    changeType: 'positive',
    accentColor: '#F59E0B',
  },
  {
    icon: Activity,
    label: 'Amount Blocked',
    value: '₹4.2Cr',
    change: '8.1%',
    changeType: 'positive',
    accentColor: '#10B981',
  },
];

export default function DashboardPage() {
  return (
    <div className={styles.dashboard}>
      {/* Page Header */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Dashboard</h1>
          <p className={styles.pageSubtitle}>Real-time fraud detection overview</p>
        </div>
        <div className={styles.headerActions}>
          <span className={styles.lastUpdated}>
            Last updated: <strong>Just now</strong>
          </span>
        </div>
      </div>

      {/* Stats Row */}
      <div className={styles.statsGrid}>
        {STATS.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>

      {/* Charts Row */}
      <div className={styles.chartsRow}>
        <div className={styles.mainChart}>
          <TransactionChart />
        </div>
        <div className={styles.sidePanel}>
          <RiskDistribution />
        </div>
      </div>

      {/* Alerts + Table */}
      <div className={styles.bottomRow}>
        <div className={styles.alertsPanel}>
          <AlertFeed />
        </div>
        <div className={styles.tablePanel}>
          <RecentTransactions />
        </div>
      </div>
    </div>
  );
}
