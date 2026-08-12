'use client';

import styles from './RecentTransactions.module.css';

const TRANSACTIONS = [
  { id: 'TXN-84729103', user: 'Priya Sharma', amount: 245000, category: 'Electronics', method: 'Card', risk: 89, status: 'BLOCKED', time: '2:14 AM' },
  { id: 'TXN-39281746', user: 'Rahul Verma', amount: 18500, category: 'Travel', method: 'UPI', risk: 62, status: 'REVIEW', time: '2:12 AM' },
  { id: 'TXN-92847561', user: 'Anita Desai', amount: 4200, category: 'Groceries', method: 'Card', risk: 8, status: 'APPROVED', time: '2:10 AM' },
  { id: 'TXN-12983745', user: 'Vikram Singh', amount: 87000, category: 'Jewelry', method: 'NetBanking', risk: 74, status: 'REVIEW', time: '2:08 AM' },
  { id: 'TXN-56483920', user: 'Meera Patel', amount: 1500, category: 'Food', method: 'UPI', risk: 5, status: 'APPROVED', time: '2:06 AM' },
  { id: 'TXN-73829461', user: 'Arjun Nair', amount: 156000, category: 'Gaming', method: 'Card', risk: 91, status: 'BLOCKED', time: '2:04 AM' },
  { id: 'TXN-28374619', user: 'Deepa Kumar', amount: 32000, category: 'Shopping', method: 'Wallet', risk: 34, status: 'APPROVED', time: '2:02 AM' },
  { id: 'TXN-94827361', user: 'Suresh Iyer', amount: 9800, category: 'Utilities', method: 'UPI', risk: 12, status: 'APPROVED', time: '2:00 AM' },
];

function getRiskClass(score) {
  if (score >= 70) return 'risk-high';
  if (score >= 30) return 'risk-medium';
  return 'risk-low';
}

function getStatusClass(status) {
  switch (status) {
    case 'BLOCKED': return 'badge-high';
    case 'REVIEW': return 'badge-medium';
    case 'APPROVED': return 'badge-low';
    default: return 'badge-info';
  }
}

function formatAmount(amt) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amt);
}

export default function RecentTransactions() {
  return (
    <div className={styles.tableCard}>
      <div className={styles.header}>
        <h3 className={styles.title}>Recent Transactions</h3>
        <button className="btn btn-ghost">View All</button>
      </div>
      <div className={styles.tableWrap}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Transaction ID</th>
              <th>User</th>
              <th>Amount</th>
              <th>Category</th>
              <th>Method</th>
              <th>Risk Score</th>
              <th>Status</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {TRANSACTIONS.map((txn) => (
              <tr key={txn.id}>
                <td><span className="mono">{txn.id}</span></td>
                <td style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{txn.user}</td>
                <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{formatAmount(txn.amount)}</td>
                <td>{txn.category}</td>
                <td>{txn.method}</td>
                <td>
                  <div className={styles.riskCell}>
                    <span className={styles.riskValue}>{txn.risk}</span>
                    <div className={`risk-bar ${getRiskClass(txn.risk)}`}>
                      <div className="risk-bar-fill" style={{ width: `${txn.risk}%` }} />
                    </div>
                  </div>
                </td>
                <td><span className={`badge ${getStatusClass(txn.status)}`}>{txn.status}</span></td>
                <td className="mono">{txn.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
