'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import styles from './RiskDistribution.module.css';

const RISK_DATA = [
  { name: 'Low Risk', value: 78, color: '#10B981' },
  { name: 'Medium Risk', value: 16, color: '#F59E0B' },
  { name: 'High Risk', value: 6, color: '#EF4444' },
];

export default function RiskDistribution() {
  const total = RISK_DATA.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Risk Distribution</h3>
      <div className={styles.chartWrap}>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={RISK_DATA}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={85}
              paddingAngle={3}
              dataKey="value"
              stroke="none"
            >
              {RISK_DATA.map((entry, idx) => (
                <Cell key={idx} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: 'rgba(17,24,39,0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#F1F5F9',
              }}
              formatter={(value) => [`${value}%`, null]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className={styles.centerLabel}>
          <span className={styles.centerValue}>{total}%</span>
          <span className={styles.centerText}>Scored</span>
        </div>
      </div>
      <div className={styles.legend}>
        {RISK_DATA.map((entry) => (
          <div key={entry.name} className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: entry.color }} />
            <span className={styles.legendName}>{entry.name}</span>
            <span className={styles.legendValue}>{entry.value}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
