'use client';

import { Users, UserPlus, Shield, Activity } from 'lucide-react';
import styles from '../page.module.css';

const USERS_DATA = [
  { id: 'USR-001', name: 'Admin Account', email: 'admin@fraudshield.ai', role: 'admin', status: 'Active', lastLogin: '2 mins ago' },
  { id: 'USR-002', name: 'John Doe', email: 'john@fraudshield.ai', role: 'analyst', status: 'Active', lastLogin: '1 hr ago' },
  { id: 'USR-003', name: 'Sarah Smith', email: 'sarah@fraudshield.ai', role: 'analyst', status: 'Offline', lastLogin: '1 day ago' },
];

export default function UsersPage() {
  return (
    <div className={styles.dashboard}>
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>User Management</h1>
          <p className={styles.pageSubtitle}>Manage admins and fraud analysts</p>
        </div>
        <div className={styles.headerActions}>
          <button className="btn btn-primary"><UserPlus size={18} /> Add User</button>
        </div>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>User ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Last Login</th>
            </tr>
          </thead>
          <tbody>
            {USERS_DATA.map((u) => (
              <tr key={u.id}>
                <td className="mono">{u.id}</td>
                <td style={{fontWeight: 500}}>{u.name}</td>
                <td>{u.email}</td>
                <td>
                  <span className={`badge ${u.role === 'admin' ? 'badge-high' : 'badge-info'}`}>
                    {u.role.toUpperCase()}
                  </span>
                </td>
                <td>
                  <span className={`badge ${u.status === 'Active' ? 'badge-low' : 'badge-medium'}`}>
                    {u.status}
                  </span>
                </td>
                <td className="mono">{u.lastLogin}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
