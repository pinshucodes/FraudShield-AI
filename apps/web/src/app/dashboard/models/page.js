'use client';

import React from 'react';
import styles from './page.module.css';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Cpu, Settings, Play, Database, Server } from 'lucide-react';

const trainingHistory = [
  { run: 'Run 1', f1: 0.85, auc: 0.91 },
  { run: 'Run 2', f1: 0.88, auc: 0.94 },
  { run: 'Run 3', f1: 0.89, auc: 0.95 },
  { run: 'Run 4', f1: 0.90, auc: 0.97 },
  { run: 'Run 5', f1: 0.918, auc: 0.987 },
];

const featureImportance = [
  { feature: 'Txn Amount', score: 0.95 },
  { feature: 'Time of Day', score: 0.82 },
  { feature: 'IP Velocity', score: 0.78 },
  { feature: 'Device Age', score: 0.65 },
  { feature: 'Geo Distance', score: 0.61 },
  { feature: 'Past Txn Cnt', score: 0.54 },
  { feature: 'Mcc Code', score: 0.45 },
  { feature: 'Payee History', score: 0.40 },
  { feature: 'Auth Method', score: 0.35 },
  { feature: 'Card Type', score: 0.22 },
];

const modelsList = [
  { name: 'XGBoost v2.1', type: 'Ensemble', acc: '96.8%', prec: '94.2%', rec: '89.5%', f1: '91.8%', auc: '0.987', status: 'Active' },
  { name: 'Random Forest', type: 'Ensemble', acc: '94.5%', prec: '91.0%', rec: '85.2%', f1: '88.0%', auc: '0.954', status: 'Standby' },
  { name: 'LightGBM v1.0', type: 'Gradient Boost', acc: '95.2%', prec: '92.5%', rec: '87.1%', f1: '89.7%', auc: '0.971', status: 'Evaluating' },
  { name: 'Logistic Regression', type: 'Linear', acc: '88.1%', prec: '82.4%', rec: '75.6%', f1: '78.8%', auc: '0.890', status: 'Archived' },
];

export default function ModelsPage() {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Machine Learning Models</h1>
          <p className={styles.subtitle}>Manage, deploy, and evaluate fraud detection models</p>
        </div>
        <div className={styles.actions}>
          <button className="btn" style={{ background: 'rgba(255,255,255,0.05)' }}>
            <Settings size={16} />
            AutoML Settings
          </button>
          <button className="btn" style={{ background: '#3B82F6', color: '#fff', border: 'none' }}>
            <Play size={16} />
            Train New Model
          </button>
        </div>
      </div>

      <div className={`glass-card ${styles.currentModelCard}`}>
        <div className={styles.modelHeader}>
          <div className={styles.modelTitleGroup}>
            <div className={styles.modelIcon}>
              <Cpu size={24} color="#3B82F6" />
            </div>
            <div>
              <h2 className={styles.modelName}>XGBoost Fraud Classifier v2.1</h2>
              <p className={styles.modelDesc}>Production Model • Deployed: 12 Aug 2026 • Trained on 4.2M records</p>
            </div>
          </div>
          <span className={`badge ${styles.badgeActive}`}>Production Active</span>
        </div>
        
        <div className={styles.metricsGrid}>
          <div className={styles.metricBox}>
            <span className={styles.metricLabel}>Inference Time</span>
            <span className={styles.metricValue}>12.4 ms</span>
          </div>
          <div className={styles.metricBox}>
            <span className={styles.metricLabel}>Throughput</span>
            <span className={styles.metricValue}>1,450 req/s</span>
          </div>
          <div className={styles.metricBox}>
            <span className={styles.metricLabel}>Memory Footprint</span>
            <span className={styles.metricValue}>420 MB</span>
          </div>
          <div className={styles.metricBox}>
            <span className={styles.metricLabel}>Feature Count</span>
            <span className={styles.metricValue}>128</span>
          </div>
        </div>
      </div>

      <div className={styles.chartsGrid}>
        <div className={`glass-card ${styles.chartCard}`}>
          <h3 className={styles.sectionTitle}>Training History (F1 & AUC)</h3>
          <div className={styles.chartWrapper}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trainingHistory} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="run" stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748B" fontSize={12} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                <Tooltip 
                  contentStyle={{ background: '#0F172A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                />
                <Line type="monotone" dataKey="f1" stroke="#3B82F6" strokeWidth={3} dot={{ r: 4, fill: '#3B82F6' }} name="F1 Score" />
                <Line type="monotone" dataKey="auc" stroke="#10B981" strokeWidth={3} dot={{ r: 4, fill: '#10B981' }} name="AUC-ROC" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className={`glass-card ${styles.chartCard}`}>
          <h3 className={styles.sectionTitle}>Top 10 Feature Importance (SHAP)</h3>
          <div className={styles.chartWrapper}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={featureImportance} layout="vertical" margin={{ top: 0, right: 10, bottom: 0, left: 20 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="feature" type="category" stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  contentStyle={{ background: '#0F172A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                />
                <Bar dataKey="score" fill="#8B5CF6" radius={[0, 4, 4, 0]} barSize={12} name="Importance Score" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className={`glass-card ${styles.tableCard}`}>
        <h3 className={styles.sectionTitle} style={{ padding: '20px 20px 0 20px' }}>Model Comparison Directory</h3>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Model Name</th>
                <th>Type</th>
                <th>Accuracy</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1 Score</th>
                <th>AUC</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {modelsList.map((model, idx) => (
                <tr key={idx}>
                  <td className={styles.modelNameCell}>
                    <Database size={14} className={styles.cellIcon} />
                    {model.name}
                  </td>
                  <td>{model.type}</td>
                  <td>{model.acc}</td>
                  <td>{model.prec}</td>
                  <td>{model.rec}</td>
                  <td>{model.f1}</td>
                  <td>{model.auc}</td>
                  <td>
                    <span className={`badge ${
                      model.status === 'Active' ? styles.badgeActive : 
                      model.status === 'Evaluating' ? styles.badgeEvaluating : 
                      model.status === 'Standby' ? styles.badgeStandby : styles.badgeArchived
                    }`}>
                      {model.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
