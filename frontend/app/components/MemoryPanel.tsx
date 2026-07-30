import React from 'react';
import styles from './MemoryPanel.module.css';
import { User, Issue } from '../types';
import { Toast } from './Toast';

// Props received from the parent component
interface MemoryPanelProps {
  currentUser: User;
  sessionId: string;
  sessionCount: number;
  live1: string | null;
  live2: string | null;
  openPlus: number;
  dynMood: { mood: string; cls: string } | null;
  backendIssues: Issue[];
  onClearMemory: () => void;
}

export function MemoryPanel({
  currentUser,
  sessionId,
  sessionCount,
  live1,
  live2,
  openPlus,
  dynMood,
  backendIssues,
  onClearMemory
}: MemoryPanelProps) {

  // If the mood changed during the conversation, display it.
  // Otherwise use the user's original mood.


  return (
    <div className={styles.mem}>

      {/* Panel Header */}
      <div className={styles.memHead}>
        <div className={styles.panelLabel}>Memory</div>
        <button className={styles.clearBtn} onClick={onClearMemory} title="Clear all stored memories">Clear</button>
      </div>

      {/* Live memory updates (temporary toast notifications) */}
      <div className={styles.liveSec}>
        <div className={styles.liveTitle}>
          <div className={styles.liveDot}></div>
          Live updates
        </div>

        <Toast message={live1} />
        <Toast message={live2} />
      </div>

      {/* ================= Issues ================= */}
      <div className={styles.msec}>
        <div className={`${styles.msecTitle} ${styles.msecTitleIss}`}>
          Issues
        </div>

        {/* If there are no existing or backend issues */}
        {currentUser.issues.length === 0 && backendIssues.length === 0 ? (
          <div
            style={{
              fontSize: '10.5px',
              color: 'var(--tx3)',
              padding: '4px 0'
            }}
          >
            No issues on record
          </div>
        ) : (
          <>
            {/* Backend-returned issues */}
            {backendIssues.map((i, idx) => (
              <div key={`be-${idx}`} className={styles.mcard}>
                <div className={styles.mcardTop}>
                  <span className={styles.mcardDate}>{i.date}</span>
                  <span className={`${styles.mbadge} ${i.badge === 'res' ? styles.mbadgeRes : styles.mbadgeOpen}`}>
                    {i.badge === 'res' ? 'resolved' : 'open'}
                  </span>
                </div>
                <div className={styles.mcardTxt} dangerouslySetInnerHTML={{ __html: i.text }} />
              </div>
            ))}
            {/* Existing issues already stored for this customer */}
            {currentUser.issues.map((i, idx) => (
              <div key={idx} className={styles.mcard}>
                <div className={styles.mcardTop}>

                  <span className={styles.mcardDate}>
                    {i.date}
                  </span>

                  {/* Badge changes color and text depending on status */}
                  <span
                    className={`${styles.mbadge} ${i.badge === 'res'
                        ? styles.mbadgeRes
                        : styles.mbadgeOpen
                      }`}
                  >
                    {i.badge === 'res' ? 'resolved' : 'open'}
                  </span>

                </div>

                {/* Render HTML stored inside the issue text */}
                <div
                  className={styles.mcardTxt}
                  dangerouslySetInnerHTML={{ __html: i.text }}
                />
              </div>
            ))}
          </>
        )}
      </div>

      {/* ================= Preferences ================= */}
      <div className={styles.msec}>
        <div className={`${styles.msecTitle} ${styles.msecTitlePrf}`}>
          Preferences
        </div>

        {/* No stored preferences */}
        {currentUser.prefs.length === 0 ? (
          <div
            style={{
              fontSize: '10.5px',
              color: 'var(--tx3)',
              padding: '4px 0'
            }}
          >
            No preferences stored
          </div>
        ) : (
          // Display each stored preference
          currentUser.prefs.map((p, idx) => (
            <div key={idx} className={styles.mcard}>
              <div className={styles.mcardTop}>
                <span className={styles.mcardDate}>
                  stored
                </span>

                <span className={`${styles.mbadge} ${styles.mbadgePref}`}>
                  pref
                </span>
              </div>

              <div
                className={styles.mcardTxt}
                dangerouslySetInnerHTML={{ __html: p.text }}
              />
            </div>
          ))
        )}
      </div>

      {/* ================= Statistics ================= */}
      <div className={styles.msec}>
        <div className={`${styles.msecTitle} ${styles.msecTitleSts}`}>
          Stats
        </div>

        {/* Total conversations */}
        <div className={styles.srow}>
          <span className={styles.slabel}>Sessions</span>
          <span className={`${styles.sval} ${styles.svalT}`}>
            {sessionCount}
          </span>
        </div>

        {/* Existing + newly added issues */}
        <div className={styles.srow}>
          <span className={styles.slabel}>Open issues</span>
          <span className={styles.sval}>
            {currentUser.openIssues + openPlus}
          </span>
        </div>

        {/* Current customer sentiment */}
  

        {/* Current session ID */}
        <div className={styles.srow}>
          <span className={styles.slabel}>Session ID</span>
          <span
            className={styles.sval}
            style={{
              fontSize: '9px',
              color: 'var(--tx3)'
            }}
          >
            {sessionId}
          </span>
        </div>
      </div>
    </div>
  );
}