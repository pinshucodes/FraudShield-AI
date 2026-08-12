import { AuthProvider } from '@/context/AuthContext';
import './globals.css';

export const metadata = {
  title: 'FraudShield AI — Fraud Detection Dashboard',
  description: 'Real-time AI-powered fraud detection and risk scoring platform for financial transactions.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
