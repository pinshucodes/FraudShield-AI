'use client';

import { Download, FileText, PieChart } from 'lucide-react';
import styles from '../page.module.css';
import StatCard from '@/components/dashboard/StatCard';

const REPORT_STATS = [
  { label: 'Total Scanned', value: '1.2M', change: '+5%', changeType: 'positive', icon: FileText, accentColor: '#3b82f6' },
  { label: 'Fraud Prevented', value: '₹4.2Cr', change: '+12%', changeType: 'positive', icon: PieChart, accentColor: '#10b981' },
];

export default function ReportsPage() {
  return (
    <div className={styles.dashboard}>
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Reports & Analytics</h1>
          <p className={styles.pageSubtitle}>Generate and download aggregated fraud insights</p>
        </div>
        <div className={styles.headerActions}>
          <button className="btn btn-primary"><Download size={18} /> Export CSV</button>
        </div>
      </div>

      <div className={styles.statsGrid}>
        {REPORT_STATS.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>

      <div className="card" style={{ marginTop: '24px' }}>
        <h3 style={{ marginBottom: '16px', color: 'var(--text-primary)' }}>Monthly Fraud Loss Prevention</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          This section contains detailed analytics of fraud prevention over time. 
          Use the Export CSV button above to download the raw dataset.
        </p>
        <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
          <p style={{ color: 'var(--text-tertiary)' }}>Chart Placeholder (Use TransactionChart here if needed)</p>
        </div>
      </div>
    </div>
  );
}
