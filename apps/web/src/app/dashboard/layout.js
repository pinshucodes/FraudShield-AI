import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import ProtectedRoute from '@/components/ProtectedRoute';
import { WebSocketProvider } from '@/context/WebSocketContext';
import styles from './layout.module.css';

export default function DashboardLayout({ children }) {
  return (
    <ProtectedRoute>
      <WebSocketProvider>
        <div className={styles.dashboardLayout}>
          <Sidebar />
          <div className={styles.mainArea}>
            <Header />
            <main className={styles.content}>
              {children}
            </main>
          </div>
        </div>
      </WebSocketProvider>
    </ProtectedRoute>
  );
}
