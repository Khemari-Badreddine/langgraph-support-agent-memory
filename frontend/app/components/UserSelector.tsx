import React, { useState } from 'react';
import Image from 'next/image';
import styles from './UserSelector.module.css';
import CsaLogoPrimary from '../assets/csa_logo_primary.svg';
import { User } from '../types';
import { USERS } from '../config';

interface UserSelectorProps {
  onConfirm: (user: User) => void;
}

export function UserSelector({ onConfirm }: UserSelectorProps) {
  const [selectedIdx, setSelectedIdx] = useState(-1);
  const [customUid, setCustomUid] = useState('');

  const handleConfirm = () => {
    if (customUid.trim()) {
      const val = customUid.trim();
      onConfirm({
        id: val,
        name: val,
        initials: val.slice(0, 2).toUpperCase(),
        tag: 'new',
        tagLabel: 'New',
        color: 'linear-gradient(135deg,#1E2235,#252A42)',
        sessions: 0,
        openIssues: 0,
        issues: [],
        prefs: [],
        greeting: `Hi! I'm your support agent. What can I help you with today?`,
      });
    } else if (selectedIdx !== -1) {
      onConfirm(USERS[selectedIdx]);
    }
  };

  const canConfirm = customUid.trim().length > 0 || selectedIdx !== -1;

  return (
    <div className={styles.selector}>
      <div className={styles.selCard}>
        <div className={styles.selLogo}>
          <Image src={CsaLogoPrimary} alt="Customer Support Agent" style={{ height: '60px', width: 'auto' }} />
        </div>

        <div className={styles.selTitle}>Who are you?</div>
        <div className={styles.selSub}>
          Pick a demo account or enter a custom user ID to start a session with isolated memory.
        </div>

        <div className={styles.selLabel}>Demo accounts</div>
        <div className={styles.userList}>
          {USERS.map((u, i) => (
            <div
              key={u.id}
              className={`${styles.userCard} ${selectedIdx === i ? styles.userCardSelected : ''}`}
              onClick={() => { setSelectedIdx(i); setCustomUid(''); }}
            >
              <div className={styles.userAva} style={{ background: u.color }}>{u.initials}</div>
              <div className={styles.userInfo}>
                <div className={styles.userName}>
                  {u.name}
                  <span className={`${styles.userTag} ${u.tag === 'ret' ? styles.userTagRet : styles.userTagNew}`}>
                    {u.tagLabel}
                  </span>
                </div>
                <div className={styles.userDetail}>
                  {u.id} · {u.sessions ? `${u.sessions} past session${u.sessions > 1 ? 's' : ''}` : 'no prior history'}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className={styles.divider}>
          <div className={styles.dividerLine}></div>
          <span className={styles.dividerTxt}>or enter custom ID</span>
          <div className={styles.dividerLine}></div>
        </div>

        <div className={styles.customRow}>
          <input
            className={styles.customInp}
            value={customUid}
            placeholder="e.g. user_xyz"
            onChange={e => { setCustomUid(e.target.value); setSelectedIdx(-1); }}
            onKeyDown={e => { if (e.key === 'Enter' && canConfirm) handleConfirm(); }}
          />
          <button className={styles.selBtn} onClick={handleConfirm} disabled={!canConfirm}>
            Start
          </button>
        </div>
      </div>
    </div>
  );
}
