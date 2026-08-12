'use client';

import { AlertTriangle, TrendingUp, MapPin, Clock, Zap } from 'lucide-react';
import styles from './AlertFeed.module.css';

const ALERTS = [
  {
    id: 1,
    type: 'HIGH',
    title: 'Unusual high-value transaction',
    description: 'TXN-84729103 — ₹2,45,000 at 2:14 AM from electronics merchant',
    time: '2 min ago',
    icon: AlertTriangle,
  },
  {
    id: 2,
    type: 'HIGH',
    title: 'Velocity attack detected',
    description: '7 transactions in 3 minutes from card ending 4829',
    time: '5 min ago',
    icon: Zap,
  },
  {
    id: 3,
    type: 'MEDIUM',
    title: 'Geographic anomaly',
    description: 'Transaction in Lagos, 30 min after one in Mumbai',
    time: '12 min ago',
    icon: MapPin,
  },
  {
    id: 4,
    type: 'MEDIUM',
    title: 'Amount deviation',
    description: 'TXN-39281746 — 8.5x above user average spend',
    time: '18 min ago',
    icon: TrendingUp,
  },
  {
    id: 5,
    type: 'LOW',
    title: 'New device login',
    description: 'User USR-10234 logged in from unrecognized device',
    time: '24 min ago',
    icon: Clock,
  },
  {
    id: 6,
    type: 'HIGH',
    title: 'Card testing pattern',
    description: 'Multiple small transactions (₹1-10) on card ending 7291',
    time: '31 min ago',
    icon: AlertTriangle,
  },
];

export default function AlertFeed() {
  return (
    <div className={styles.feedCard}>
      <div className={styles.header}>
        <h3 className={styles.title}>
          <span className="status-dot danger pulse-live" />
          Live Alerts
        </h3>
        <span className={styles.count}>{ALERTS.length}</span>
      </div>
      <div className={styles.list}>
        {ALERTS.map((alert, idx) => {
          const Icon = alert.icon;
          return (
            <div
              key={alert.id}
              className={styles.alertItem}
              style={{ animationDelay: `${idx * 0.05}s` }}
            >
              <div className={`${styles.alertIcon} ${styles[`icon${alert.type}`]}`}>
                <Icon size={16} />
              </div>
              <div className={styles.alertContent}>
                <div className={styles.alertHeader}>
                  <span className={styles.alertTitle}>{alert.title}</span>
                  <span className={`badge badge-${alert.type.toLowerCase()}`}>{alert.type}</span>
                </div>
                <p className={styles.alertDesc}>{alert.description}</p>
                <span className={styles.alertTime}>{alert.time}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
