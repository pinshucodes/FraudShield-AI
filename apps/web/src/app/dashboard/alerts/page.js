'use client';

import React, { useState } from 'react';
import styles from './page.module.css';
import { Bell, ShieldAlert, AlertCircle, AlertTriangle, Info, Check, X, Search } from 'lucide-react';

const mockAlerts = [
  { id: 'ALT-1049', title: 'Suspicious IP Login Pattern', desc: 'Multiple logins from High-Risk IPs (Russia, Nigeria) within 5 minutes.', txId: 'TXN-982412', amount: null, time: '2 mins ago', severity: 'High' },
  { id: 'ALT-1050', title: 'Large Transfer Anomaly', desc: 'Transfer amount exceeds 99th percentile of user historical behavior.', txId: 'TXN-982408', amount: 850000, time: '14 mins ago', severity: 'Critical' },
  { id: 'ALT-1051', title: 'Velocity Limit Exceeded', desc: 'User triggered 15 transactions in under 2 minutes.', txId: 'TXN-982390', amount: 4500, time: '35 mins ago', severity: 'Medium' },
  { id: 'ALT-1052', title: 'New Device + New Payee', desc: 'High value transfer to new payee from unrecognized device.', txId: 'TXN-982375', amount: 125000, time: '1 hour ago', severity: 'High' },
  { id: 'ALT-1053', title: 'Card Testing Suspected', desc: 'Series of small transactions (₹1 - ₹10) declined due to CVV mismatch.', txId: 'TXN-982310', amount: 10, time: '2 hours ago', severity: 'Medium' },
  { id: 'ALT-1054', title: 'Location Mismatch', desc: 'IP location (Mumbai) differs from GPS location (Delhi) by >1000km.', txId: 'TXN-982285', amount: 45000, time: '3 hours ago', severity: 'Low' },
  { id: 'ALT-1055', title: 'Dormant Account Activity', desc: 'Account inactive for 18 months initiated a RTGS transfer.', txId: 'TXN-982220', amount: 320000, time: '4 hours ago', severity: 'High' },
  { id: 'ALT-1056', title: 'Multiple Failed OTPs', desc: '5 failed OTP attempts followed by successful transaction.', txId: 'TXN-982190', amount: 15000, time: '5 hours ago', severity: 'Medium' },
  { id: 'ALT-1057', title: 'Known Fraudulent VPA', desc: 'Beneficiary VPA matches global blocklist pattern.', txId: 'TXN-982105', amount: 2500, time: '6 hours ago', severity: 'Critical' },
  { id: 'ALT-1058', title: 'Unusual Time of Day', desc: 'Transaction at 3:15 AM, normally active between 10 AM - 8 PM.', txId: 'TXN-982050', amount: 12000, time: '8 hours ago', severity: 'Low' },
];

export default function AlertsPage() {
  const [activeTab, setActiveTab] = useState('All');

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'Critical': return <ShieldAlert size={20} color="#EF4444" />;
      case 'High': return <AlertTriangle size={20} color="#F97316" />;
      case 'Medium': return <AlertCircle size={20} color="#F59E0B" />;
      case 'Low': return <Info size={20} color="#3B82F6" />;
      default: return <Info size={20} color="#64748B" />;
    }
  };
  
  const getSeverityClass = (severity) => {
    switch (severity) {
      case 'Critical': return styles.borderCritical;
      case 'High': return styles.borderHigh;
      case 'Medium': return styles.borderMedium;
      case 'Low': return styles.borderLow;
      default: return '';
    }
  };

  const filteredAlerts = activeTab === 'All' 
    ? mockAlerts 
    : activeTab === 'Resolved' 
      ? [] 
      : mockAlerts.filter(a => a.severity === activeTab || (activeTab === 'High Priority' && (a.severity === 'High' || a.severity === 'Critical')));

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <div className={styles.titleWrapper}>
            <h1 className={styles.title}>Alert Center</h1>
            <span className={styles.alertCount}>10 Unresolved</span>
          </div>
          <p className={styles.subtitle}>Review and investigate flagged anomalous activities</p>
        </div>
        <div className={styles.searchBox}>
          <Search size={16} color="#64748B" />
          <input type="text" placeholder="Search alerts..." className={styles.searchInput} />
        </div>
      </div>

      <div className={styles.tabs}>
        {['All', 'High Priority', 'Medium', 'Low', 'Resolved'].map(tab => (
          <button 
            key={tab}
            className={`${styles.tab} ${activeTab === tab ? styles.activeTab : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className={styles.alertList}>
        {filteredAlerts.length > 0 ? (
          filteredAlerts.map(alert => (
            <div key={alert.id} className={`glass-card ${styles.alertCard} ${getSeverityClass(alert.severity)}`}>
              <div className={styles.alertIconWrapper}>
                {getSeverityIcon(alert.severity)}
              </div>
              
              <div className={styles.alertContent}>
                <div className={styles.alertHeader}>
                  <h3 className={styles.alertTitle}>{alert.title}</h3>
                  <span className={styles.alertTime}>{alert.time}</span>
                </div>
                
                <p className={styles.alertDesc}>{alert.desc}</p>
                
                <div className={styles.alertMeta}>
                  {alert.txId && (
                    <span className={styles.metaItem}>
                      <span className={styles.metaLabel}>TxID:</span> 
                      <span className={styles.metaValueMono}>{alert.txId}</span>
                    </span>
                  )}
                  {alert.amount !== null && (
                    <span className={styles.metaItem}>
                      <span className={styles.metaLabel}>Amount:</span> 
                      <span className={styles.metaValue}>₹{alert.amount.toLocaleString('en-IN')}</span>
                    </span>
                  )}
                  <span className={`${styles.severityBadge} ${styles[`badge${alert.severity}`]}`}>
                    {alert.severity} Risk
                  </span>
                </div>
              </div>
              
              <div className={styles.alertActions}>
                <button className={`btn ${styles.btnInvestigate}`}>Investigate</button>
                <div className={styles.actionRow}>
                  <button className={styles.iconBtn} title="Dismiss">
                    <X size={18} />
                  </button>
                  <button className={styles.iconBtnSuccess} title="Mark Resolved">
                    <Check size={18} />
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className={`glass-card ${styles.emptyState}`}>
            <Bell size={48} color="#64748B" className={styles.emptyIcon} />
            <h3>No Alerts Found</h3>
            <p>There are no alerts matching the current filter criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
}
