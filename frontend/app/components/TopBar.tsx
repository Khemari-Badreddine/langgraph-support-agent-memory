import React from 'react';
import Image from 'next/image';
import styles from './TopBar.module.css';
import CsaLogoPrimary from '../assets/csa_logo_primary.svg';
import { User } from '../types';

interface TopBarProps {
  currentUser: User;
  sessionId: string;
  activeAgentBadge: string;
  onNewConversation: () => void;
  onSwitchUser: () => void;
}

export function TopBar({
  currentUser,
  sessionId,
  activeAgentBadge,
  onNewConversation,
  onSwitchUser,
}: TopBarProps) {
  return (
    <div className={styles.top}>
      <div className={styles.logo}>
        <Image
          src={CsaLogoPrimary}
          alt="Customer Support Agent"
          style={{ height: '64px', width: 'auto' }}
          priority
        />
      </div>
      <div className={styles.topRight}>
        <div className={styles.dot}></div>
        <span className={styles.pill}>{currentUser.name}  ·  {sessionId}</span>
        <span className={styles.pill}>{activeAgentBadge}</span>
        <button className={styles.topBtn} onClick={onNewConversation} title="New conversation">↺ New conversation</button>
        <button className={`${styles.topBtn} ${styles.topBtnDanger}`} onClick={onSwitchUser} title="Switch user">⇄ Switch user</button>
      </div>
    </div>
  );
}
