'use client';

import React from 'react';
import styles from './page.module.css';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Shield, AlertTriangle, Activity, CheckCircle, Target, TrendingUp } from 'lucide-react';

const riskDistributionData = [
  { bin: '0-10', count: 12500, color: '#10B981' },
  { bin: '10-20', count: 8200, color: '#10B981' },
  { bin: '20-30', count: 4300, color: '#34D399' },
  { bin: '30-40', count: 2100, color: '#FCD34D' },
  { bin: '40-50', count: 1200, color: '#F59E0B' },
  { bin: '50-60', count: 850, color: '#F59E0B' },
  { bin: '60-70', count: 520, color: '#F97316' },
  { bin: '70-80', count: 310, color: '#EA580C' },
  { bin: '80-90', count: 180, color: '#EF4444' },
  { bin: '90-100', count: 95, color: '#B91C1C' },
];

const activeRules = [
  { id: 1, name: 'High Velocity Transfers', type: 'Velocity', severity: 'High', status: true, triggers: 1450 },
  { id: 2, name: 'Location Mismatch', type: 'Geolocation', severity: 'Medium', status: true, triggers: 890 },
  { id: 3, name: 'New Device Login', type: 'Device', severity: 'Low', status: true, triggers: 3200 },
  { id: 4, name: 'Unusual Amount for User', type: 'Behavioral', severity: 'High', status: true, triggers: 675 },
  { id: 5, name: 'Multiple Failed OTPs', type: 'Authentication', severity: 'High', status: true, triggers: 1120 },
  { id: 6, name: 'Off-hours High Value Txn', type: 'Temporal', severity: 'Medium', status: false, triggers: 430 },
  { id: 7, name: 'Known IP Blocklist', type: 'Network', severity: 'Critical', status: true, triggers: 89 },
  { id: 8, name: 'Card Testing Pattern', type: 'Velocity', severity: 'High', status: true, triggers: 215 },
];

export default function RiskEnginePage() {
  const getSeverityClass = (severity) => {
    switch (severity) {
      case 'Low': return styles.sevLow;
      case 'Medium': return styles.sevMedium;
      case 'High': return styles.sevHigh;
      case 'Critical': return styles.sevCritical;
      default: return '';
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Risk Engine</h1>
          <p className={styles.subtitle}>Configure scoring rules and monitor ML model performance</p>
        </div>
        <button className="btn">
          <Shield size={16} />
          Engine Settings
        </button>
      </div>

      <div className={styles.statsRow}>
        <div className={`glass-card ${styles.statCard}`}>
          <div className={styles.statIcon} style={{ color: '#3B82F6', background: 'rgba(59,130,246,0.1)' }}>
            <Activity size={24} />
          </div>
          <div className={styles.statInfo}>
            <span className={styles.statLabel}>Total Scored (24h)</span>
            <span className={styles.statValue}>24,891</span>
          </div>
        </div>
        
        <div className={`glass-card ${styles.statCard}`}>
          <div className={styles.statIcon} style={{ color: '#EF4444', background: 'rgba(239,68,68,0.1)' }}>
            <AlertTriangle size={24} />
          </div>
          <div className={styles.statInfo}>
            <span className={styles.statLabel}>High Risk Flags</span>
            <span className={styles.statValue}>1,492</span>
          </div>
        </div>

        <div className={`glass-card ${styles.statCard}`}>
          <div className={styles.statIcon} style={{ color: '#10B981', background: 'rgba(16,185,129,0.1)' }}>
            <Target size={24} />
          </div>
          <div className={styles.statInfo}>
            <span className={styles.statLabel}>Average Score</span>
            <span className={styles.statValue}>23.4</span>
          </div>
        </div>
      </div>

      <div className={styles.grid}>
        <div className={`glass-card ${styles.chartContainer}`}>
          <h3 className={styles.sectionTitle}>Risk Score Distribution</h3>
          <div className={styles.chartWrapper}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskDistributionData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                <XAxis dataKey="bin" stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  contentStyle={{ background: '#0F172A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {riskDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className={`glass-card ${styles.rulesContainer}`}>
          <div className={styles.rulesHeader}>
            <h3 className={styles.sectionTitle}>Active Rules Engine</h3>
            <span className={styles.activeCount}>8 Rules Running</span>
          </div>
          <div className={styles.rulesTableWrapper}>
            <table className={`data-table ${styles.rulesTable}`}>
              <thead>
                <tr>
                  <th>Rule Name</th>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th className={styles.rightAlign}>Triggers (24h)</th>
                </tr>
              </thead>
              <tbody>
                {activeRules.map(rule => (
                  <tr key={rule.id}>
                    <td className={styles.ruleName}>{rule.name}</td>
                    <td><span className={`badge ${styles.typeBadge}`}>{rule.type}</span></td>
                    <td><span className={`badge ${getSeverityClass(rule.severity)}`}>{rule.severity}</span></td>
                    <td>
                      <div className={`${styles.toggle} ${rule.status ? styles.toggleOn : styles.toggleOff}`}>
                        <div className={styles.toggleKnob}></div>
                      </div>
                    </td>
                    <td className={styles.rightAlign}>{rule.triggers.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className={styles.perfSection}>
        <h3 className={styles.sectionTitle}>Model Performance (XGBoost v2.1)</h3>
        <div className={styles.perfGrid}>
          <div className={`glass-card ${styles.perfCard}`}>
            <span className={styles.perfLabel}>Accuracy</span>
            <span className={styles.perfValue}>96.8%</span>
            <span className={styles.perfTrend}><TrendingUp size={14}/> +0.2%</span>
          </div>
          <div className={`glass-card ${styles.perfCard}`}>
            <span className={styles.perfLabel}>Precision</span>
            <span className={styles.perfValue}>94.2%</span>
            <span className={styles.perfTrend}><TrendingUp size={14}/> +0.5%</span>
          </div>
          <div className={`glass-card ${styles.perfCard}`}>
            <span className={styles.perfLabel}>Recall</span>
            <span className={styles.perfValue}>89.5%</span>
            <span className={styles.perfTrendDown}>-0.1%</span>
          </div>
          <div className={`glass-card ${styles.perfCard}`}>
            <span className={styles.perfLabel}>F1 Score</span>
            <span className={styles.perfValue}>91.8%</span>
            <span className={styles.perfTrend}><TrendingUp size={14}/> +0.3%</span>
          </div>
          <div className={`glass-card ${styles.perfCard}`}>
            <span className={styles.perfLabel}>AUC-ROC</span>
            <span className={styles.perfValue}>0.987</span>
            <span className={styles.perfTrendEqual}>-</span>
          </div>
        </div>
      </div>
    </div>
  );
}
