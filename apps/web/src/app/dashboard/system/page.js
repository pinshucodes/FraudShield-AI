'use client';

import { Server, Database, Box, Cpu } from 'lucide-react';
import styles from '../page.module.css';

const SYSTEM_SERVICES = [
  { name: 'FastAPI Backend', status: 'Operational', latency: '42ms', uptime: '99.99%', icon: Server },
  { name: 'PostgreSQL Database', status: 'Operational', latency: '12ms', uptime: '99.95%', icon: Database },
  { name: 'Redis Cache', status: 'Operational', latency: '2ms', uptime: '100%', icon: Box },
  { name: 'ML Flow Models', status: 'Operational', latency: '18ms', uptime: '99.9%', icon: Cpu },
];

export default function SystemPage() {
  return (
    <div className={styles.dashboard}>
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>System Health</h1>
          <p className={styles.pageSubtitle}>Monitor microservices and infrastructure</p>
        </div>
      </div>

      <div className={styles.statsGrid}>
        {SYSTEM_SERVICES.map((svc) => (
          <div key={svc.name} className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '12px', borderRadius: '12px' }}>
                <svc.icon size={24} color="#3b82f6" />
              </div>
              <div>
                <h3 style={{ color: 'var(--text-primary)', fontSize: '1.1rem', fontWeight: 600 }}>{svc.name}</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)' }}></div>
                  <span style={{ color: 'var(--success)', fontSize: '0.85rem' }}>{svc.status}</span>
                </div>
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', borderTop: '1px solid var(--border-light)', paddingTop: '16px' }}>
              <div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Latency</p>
                <p style={{ color: 'var(--text-primary)', fontSize: '1.1rem', fontWeight: 600, marginTop: '4px' }}>{svc.latency}</p>
              </div>
              <div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Uptime</p>
                <p style={{ color: 'var(--text-primary)', fontSize: '1.1rem', fontWeight: 600, marginTop: '4px' }}>{svc.uptime}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
