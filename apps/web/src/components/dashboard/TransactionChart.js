'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import styles from './TransactionChart.module.css';

const CHART_DATA = [
  { time: '00:00', transactions: 1240, flagged: 12, amount: 245000 },
  { time: '02:00', transactions: 680, flagged: 8, amount: 134000 },
  { time: '04:00', transactions: 420, flagged: 15, amount: 89000 },
  { time: '06:00', transactions: 890, flagged: 6, amount: 178000 },
  { time: '08:00', transactions: 2100, flagged: 18, amount: 420000 },
  { time: '10:00', transactions: 3400, flagged: 24, amount: 680000 },
  { time: '12:00', transactions: 4200, flagged: 31, amount: 840000 },
  { time: '14:00', transactions: 3800, flagged: 28, amount: 760000 },
  { time: '16:00', transactions: 3200, flagged: 22, amount: 640000 },
  { time: '18:00', transactions: 4500, flagged: 35, amount: 900000 },
  { time: '20:00', transactions: 3900, flagged: 29, amount: 780000 },
  { time: '22:00', transactions: 2600, flagged: 20, amount: 520000 },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload) return null;
  return (
    <div className={styles.tooltip}>
      <p className={styles.tooltipLabel}>{label}</p>
      {payload.map((entry, i) => (
        <div key={i} className={styles.tooltipRow}>
          <span className={styles.tooltipDot} style={{ background: entry.color }} />
          <span className={styles.tooltipName}>{entry.name}:</span>
          <span className={styles.tooltipValue}>
            {entry.name === 'Amount' ? `₹${(entry.value / 1000).toFixed(0)}K` : entry.value.toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
};

export default function TransactionChart() {
  return (
    <div className={styles.chartCard}>
      <div className={styles.header}>
        <div>
          <h3 className={styles.title}>Transaction Volume</h3>
          <p className={styles.subtitle}>Real-time transaction monitoring</p>
        </div>
        <div className={styles.controls}>
          <button className={`${styles.controlBtn} ${styles.active}`}>24H</button>
          <button className={styles.controlBtn}>7D</button>
          <button className={styles.controlBtn}>30D</button>
        </div>
      </div>
      <div className={styles.chartWrap}>
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart data={CHART_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="txnGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="flagGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis
              dataKey="time"
              stroke="rgba(255,255,255,0.2)"
              tick={{ fill: '#64748B', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
            />
            <YAxis
              stroke="rgba(255,255,255,0.2)"
              tick={{ fill: '#64748B', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="transactions"
              name="Transactions"
              stroke="#3B82F6"
              strokeWidth={2}
              fill="url(#txnGradient)"
            />
            <Area
              type="monotone"
              dataKey="flagged"
              name="Flagged"
              stroke="#EF4444"
              strokeWidth={2}
              fill="url(#flagGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
