import { getSentimentColor, getStatusBadgeColor } from "../utils";
import type { Issue, Preference, Stats } from "../types";
import styles from "./MemoryPanel.module.css";

interface MemoryPanelProps {
  issues: Issue[];
  preferences: Preference[];
  stats: Stats;
}

export function MemoryPanel({ issues, preferences, stats }: MemoryPanelProps) {
  return (
    <div className={styles.memoryPanel}>
      <div className={styles.memoryTitleWrap}>
        <h2 className={styles.memoryTitle}>Memory</h2>
      </div>

      <div className={styles.memorySection}>
        <h3 className={`${styles.sectionLabel} ${styles.sectionIssues}`}>Issues</h3>
        <div className={styles.stack}>
          {issues.map((issue) => (
            <div
              key={issue.id}
              className={`${styles.card} ${issue.status === "new" ? styles.cardNew : ""}`}>
              <div className={styles.cardHead}>
                <span className={styles.cardDate}>{issue.date}</span>
                <span className={`${styles.issueBadge} ${styles[getStatusBadgeColor(issue.status)]}`}>
                  {issue.status}
                </span>
              </div>
              <p className={styles.cardText} dangerouslySetInnerHTML={{ __html: issue.text }} />
            </div>
          ))}
        </div>
      </div>

      <div className={styles.memorySection}>
        <h3 className={`${styles.sectionLabel} ${styles.sectionPrefs}`}>Preferences</h3>
        <div className={styles.stack}>
          {preferences.map((preference) => (
            <div key={preference.id} className={styles.card}>
              <div className={styles.cardHead}>
                <span className={styles.cardDate}>stored</span>
                <span className={styles.prefBadge}>pref</span>
              </div>
              <p className={styles.cardText} dangerouslySetInnerHTML={{ __html: preference.text }} />
            </div>
          ))}
        </div>
      </div>

      <div className={styles.memorySection}>
        <h3 className={`${styles.sectionLabel} ${styles.sectionStats}`}>Stats</h3>
        <div className={styles.statList}>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Sessions</span>
            <span className={`${styles.statValue} ${styles.statTeal}`}>{stats.sessions}</span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Open issues</span>
            <span className={styles.statValue}>{stats.openIssues}</span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Sentiment</span>
            <span className={`${styles.statValue} ${styles[getSentimentColor(stats.sentimentColor)]}`}>
              {stats.sentiment}
            </span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Last seen</span>
            <span className={styles.statValue}>2d ago</span>
          </div>
        </div>
      </div>
    </div>
  );
}
