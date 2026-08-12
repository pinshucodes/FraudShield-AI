import styles from './StatCard.module.css';

export default function StatCard({ icon: Icon, label, value, change, changeType, accentColor }) {
  return (
    <div className={styles.card} style={{ '--accent-color': accentColor }}>
      <div className={styles.iconWrap} style={{ background: `${accentColor}15`, color: accentColor }}>
        <Icon size={22} />
      </div>
      <div className={styles.content}>
        <span className={styles.label}>{label}</span>
        <span className={styles.value}>{value}</span>
        {change && (
          <span className={`${styles.change} ${changeType === 'positive' ? styles.positive : styles.negative}`}>
            {changeType === 'positive' ? '↑' : '↓'} {change}
          </span>
        )}
      </div>
      <div className={styles.glow} />
    </div>
  );
}
