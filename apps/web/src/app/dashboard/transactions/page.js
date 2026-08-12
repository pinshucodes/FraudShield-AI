'use client';

import React, { useState } from 'react';
import styles from './page.module.css';
import { Search, Filter, Download, ChevronLeft, ChevronRight, ArrowUpDown } from 'lucide-react';

const mockTransactions = [
  { id: 'TXN-982374', user: 'Rahul Sharma', amount: 45000, category: 'E-commerce', method: 'UPI', risk: 12, status: 'Completed', time: '10:42 AM' },
  { id: 'TXN-982375', user: 'Priya Patel', amount: 125000, category: 'Transfer', method: 'NEFT', risk: 85, status: 'Flagged', time: '10:45 AM' },
  { id: 'TXN-982376', user: 'Amit Kumar', amount: 3200, category: 'Food', method: 'Credit Card', risk: 5, status: 'Completed', time: '10:51 AM' },
  { id: 'TXN-982377', user: 'Sneha Gupta', amount: 89000, category: 'Electronics', method: 'Debit Card', risk: 42, status: 'Pending', time: '11:03 AM' },
  { id: 'TXN-982378', user: 'Vikram Singh', amount: 1500, category: 'Transport', method: 'UPI', risk: 2, status: 'Completed', time: '11:15 AM' },
  { id: 'TXN-982379', user: 'Neha Desai', amount: 250000, category: 'Investment', method: 'RTGS', risk: 92, status: 'Blocked', time: '11:30 AM' },
  { id: 'TXN-982380', user: 'Karan Malhotra', amount: 7500, category: 'Utility', method: 'UPI', risk: 8, status: 'Completed', time: '11:42 AM' },
  { id: 'TXN-982381', user: 'Pooja Reddy', amount: 62000, category: 'Travel', method: 'Credit Card', risk: 28, status: 'Completed', time: '12:05 PM' },
  { id: 'TXN-982382', user: 'Sanjay Verma', amount: 18000, category: 'Shopping', method: 'Debit Card', risk: 15, status: 'Completed', time: '12:18 PM' },
  { id: 'TXN-982383', user: 'Anjali Joshi', amount: 450000, category: 'Transfer', method: 'IMPS', risk: 78, status: 'Flagged', time: '12:35 PM' },
  { id: 'TXN-982384', user: 'Ravi Teja', amount: 2200, category: 'Groceries', method: 'UPI', risk: 3, status: 'Completed', time: '01:10 PM' },
  { id: 'TXN-982385', user: 'Meera Nair', amount: 135000, category: 'Jewelry', method: 'Credit Card', risk: 65, status: 'Pending', time: '01:25 PM' },
  { id: 'TXN-982386', user: 'Rajesh Khanna', amount: 500, category: 'Mobile Recharge', method: 'UPI', risk: 1, status: 'Completed', time: '01:40 PM' },
  { id: 'TXN-982387', user: 'Anita Yadav', amount: 95000, category: 'Medical', method: 'NEFT', risk: 22, status: 'Completed', time: '02:05 PM' },
  { id: 'TXN-982388', user: 'Gaurav Chawla', amount: 320000, category: 'Transfer', method: 'RTGS', risk: 88, status: 'Blocked', time: '02:22 PM' },
];

export default function TransactionsPage() {
  const [selectedRow, setSelectedRow] = useState(null);

  const getStatusClass = (status) => {
    switch (status) {
      case 'Completed': return styles.statusSuccess;
      case 'Pending': return styles.statusWarning;
      case 'Flagged': return styles.statusDanger;
      case 'Blocked': return styles.statusCritical;
      default: return '';
    }
  };

  const getRiskColor = (risk) => {
    if (risk < 20) return '#10B981';
    if (risk < 60) return '#F59E0B';
    return '#EF4444';
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Transaction Explorer</h1>
          <p className={styles.subtitle}>Real-time monitoring and analysis of all platform transactions</p>
        </div>
        <button className="btn">
          <Download size={16} />
          Export CSV
        </button>
      </div>

      <div className={`glass-card ${styles.filterBar}`}>
        <div className={styles.searchGroup}>
          <Search size={18} className={styles.searchIcon} />
          <input type="text" placeholder="Search by ID, User, or Category..." className={styles.searchInput} />
        </div>
        
        <div className={styles.filterGroup}>
          <select className={styles.select}>
            <option value="">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="flagged">Flagged</option>
            <option value="blocked">Blocked</option>
          </select>
          
          <select className={styles.select}>
            <option value="">Risk Level</option>
            <option value="low">Low (0-20)</option>
            <option value="medium">Medium (21-60)</option>
            <option value="high">High (61-100)</option>
          </select>
          
          <select className={styles.select}>
            <option value="">Amount Range</option>
            <option value="0-10000">₹0 - ₹10,000</option>
            <option value="10001-100000">₹10,001 - ₹1,00,000</option>
            <option value="100001+">₹1,00,001+</option>
          </select>
          
          <button className={`btn ${styles.filterBtn}`}>
            <Filter size={16} />
            Filter
          </button>
        </div>
      </div>

      <div className={`glass-card ${styles.tableContainer}`}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Transaction ID</th>
              <th>User</th>
              <th className={styles.rightAlign}>Amount <ArrowUpDown size={14} className={styles.sortIcon}/></th>
              <th>Category</th>
              <th>Method</th>
              <th>Risk Score <ArrowUpDown size={14} className={styles.sortIcon}/></th>
              <th>Status</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {mockTransactions.map((txn) => (
              <tr 
                key={txn.id} 
                className={selectedRow === txn.id ? styles.selectedRow : ''}
                onClick={() => setSelectedRow(txn.id)}
              >
                <td className={styles.mono}>{txn.id}</td>
                <td>{txn.user}</td>
                <td className={styles.rightAlign}>
                  ₹{txn.amount.toLocaleString('en-IN')}
                </td>
                <td>{txn.category}</td>
                <td>{txn.method}</td>
                <td>
                  <div className={styles.riskCell}>
                    <span className={styles.riskValue}>{txn.risk}</span>
                    <div className="risk-bar" style={{ width: '60px', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${txn.risk}%`, height: '100%', background: getRiskColor(txn.risk) }}></div>
                    </div>
                  </div>
                </td>
                <td>
                  <span className={`badge ${getStatusClass(txn.status)}`}>
                    {txn.status}
                  </span>
                </td>
                <td className={styles.time}>{txn.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className={styles.pagination}>
        <span className={styles.pageInfo}>Showing 1-15 of 2,847 results</span>
        <div className={styles.pageControls}>
          <button className={styles.pageBtn} disabled><ChevronLeft size={16} /></button>
          <button className={`${styles.pageBtn} ${styles.activePage}`}>1</button>
          <button className={styles.pageBtn}>2</button>
          <button className={styles.pageBtn}>3</button>
          <span className={styles.pageEllipsis}>...</span>
          <button className={styles.pageBtn}>190</button>
          <button className={styles.pageBtn}><ChevronRight size={16} /></button>
        </div>
      </div>
    </div>
  );
}
