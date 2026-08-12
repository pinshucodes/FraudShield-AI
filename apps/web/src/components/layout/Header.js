'use client';

import { Search, Bell, ChevronDown } from 'lucide-react';
import styles from './Header.module.css';

export default function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.searchContainer}>
        <Search size={18} className={styles.searchIcon} />
        <input
          type="text"
          placeholder="Search transactions, users, rules..."
          className={styles.searchInput}
        />
        <kbd className={styles.searchShortcut}>⌘K</kbd>
      </div>

      <div className={styles.actions}>
        {/* Live indicator */}
        <div className={styles.liveIndicator}>
          <span className="status-dot active pulse-live" />
          <span className={styles.liveText}>Live</span>
        </div>

        {/* Notifications */}
        <button className={styles.iconBtn} aria-label="Notifications">
          <Bell size={20} />
          <span className={styles.notifDot} />
        </button>

        {/* User */}
        <button className={styles.userBtn}>
          <div className={styles.avatar}>AK</div>
          <div className={styles.userInfo}>
            <span className={styles.userName}>Arjun Kumar</span>
            <span className={styles.userRole}>Admin</span>
          </div>
          <ChevronDown size={16} />
        </button>
      </div>
    </header>
  );
}
