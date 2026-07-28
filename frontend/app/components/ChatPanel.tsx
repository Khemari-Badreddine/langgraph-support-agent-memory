import React from 'react';
import styles from './ChatPanel.module.css';
import { User, Message } from '../types';

interface ChatPanelProps {
  currentUser: User;
  sessionCount: number;
  messages: Message[];
  isTyping: boolean;
  inputValue: string;
  onInputChange: (val: string) => void;
  onSendMessage: (msg?: string) => void;
  openTraces: Record<number, boolean>;
  onToggleTrace: (id: number) => void;
  msgsEndRef: React.RefObject<HTMLDivElement | null>;
}

export function ChatPanel({
  currentUser,
  sessionCount,
  messages,
  isTyping,
  inputValue,
  onInputChange,
  onSendMessage,
  openTraces,
  onToggleTrace,
  msgsEndRef
}: ChatPanelProps) {
  
  const getAgentAvatar = (cls: string, icon: string) => {
    const map: any = { billing: 'var(--tq)', tech: 'var(--bq)', order: 'var(--aq)', none: 'var(--s3)', triage: 'var(--pq)' };
    const cmap: any = { billing: '#00E5A0', tech: '#60A5FA', order: '#FBBF24', none: 'var(--tx3)', triage: '#A78BFA' };
    const bg = map[cls] || map.none;
    const col = cmap[cls] || cmap.none;
    return (
      <div className={styles.agentAv} style={{ background: bg, border: `1px solid ${col}22`, fontSize: '11px', color: col }}>
        {icon}
      </div>
    );
  };

  const traceIcons: any = { thought: '🧠', tool: '🔧', result: '📄', memory: '✦', action: '✅' };
  
  const getTraceKeyClass = (k: string) => {
    if (k === 'thought') return styles.traceKeyThought;
    if (k === 'tool') return styles.traceKeyTool;
    if (k === 'result') return styles.traceKeyResult;
    if (k === 'memory') return styles.traceKeyMemory;
    if (k === 'action') return styles.traceKeyAction;
    return '';
  };

  return (
    <div className={styles.chat}>
      <div className={styles.chatHead}>
        <div className={styles.ava} style={{ background: currentUser.color }}>{currentUser.initials}</div>
        <div>
          <div className={styles.avaName}>
            {currentUser.name} 
            <span className={`${styles.tag} ${currentUser.tag === 'ret' ? styles.tagRet : styles.tagNew}`}>
              {currentUser.tagLabel}
            </span>
          </div>
          <div className={styles.avaSub}>
            {sessionCount} session{sessionCount !== 1 ? 's' : ''} · Memory {messages.length === 0 ? 'still active' : 'active'}
          </div>
        </div>
      </div>

      <div className={`${styles.emptyState} ${messages.length === 0 ? styles.emptyStateShow : ''}`}>
        <div className={styles.emptyIcon}>💬</div>
        <div className={styles.emptyTitle}>New conversation</div>
        <div className={styles.emptySub}>Memory from past sessions is still active. Send a message to continue.</div>
      </div>

      <div className={styles.msgs}>
        {messages.map(m => (
          <div key={m.id} className={`${styles.msgGroup} ${styles.si}`}>
            {m.type === 'user' ? (
              <div className={`${styles.row} ${styles.rowUser}`}>
                <div>
                  <div className={styles.bbl}>{m.text}</div>
                  <div className={`${styles.ts} ${styles.tsUser}`}>{m.time}</div>
                </div>
              </div>
            ) : (
              <>
                <div className={`${styles.row} ${styles.rowAgent}`}>
                  {getAgentAvatar(m.agentInfo?.iconCls || 'none', m.agentInfo?.icon || '⬡')}
                  <div>
                    <div className={styles.bbl}>{m.text}</div>
                    <div className={styles.ts}>{m.time}</div>
                  </div>
                </div>
                {m.agentInfo?.cls === 'triageOnly' ? (
                  <div className={`${styles.routeBadge} ${styles.routeBadgeTriageOnly}`}>
                    <span>⬡</span><span className={styles.agentName}>Triage</span>
                  </div>
                ) : m.agentInfo ? (
                  <div className={`${styles.routeBadge} ${m.agentInfo.cls === 'billing' ? styles.routeBadgeBilling : m.agentInfo.cls === 'tech' ? styles.routeBadgeTech : m.agentInfo.cls === 'order' ? styles.routeBadgeOrder : ''}`}>
                    <span>⬡</span><span style={{ color: 'var(--purple)' }}>Triage</span><span style={{ margin: '0 3px' }}>→</span><span className={styles.agentName}>{m.agentInfo.specialist}</span>
                  </div>
                ) : null}
                
                {m.agentInfo?.trace && (
                  <>
                    <span className={styles.traceToggle} onClick={() => onToggleTrace(m.id)}>
                      {openTraces[m.id] ? '▼ Hide trace' : '▶ View trace'}
                    </span>
                    <div className={`${styles.traceBox} ${openTraces[m.id] ? styles.traceBoxOpen : ''}`}>
                      {m.agentInfo.trace.map((l, idx) => (
                        <div key={idx} className={styles.traceLine}>
                          <span className={styles.traceIcon}>{traceIcons[l.k] || '·'}</span>
                          <span className={`${styles.traceKey} ${getTraceKeyClass(l.k)}`}>[{l.k}]</span>&nbsp;
                          <span>{l.l}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        ))}
        {isTyping && (
          <div className={styles.typingRow}>
            <div className={styles.agentAv} style={{ background: 'var(--s3)', fontSize: '10px', color: 'var(--tx3)' }}>⬡</div>
            <div className={styles.dots}><span></span><span></span><span></span></div>
          </div>
        )}
        <div ref={msgsEndRef} />
      </div>

      <div className={styles.qrow}>
        <button className={styles.qb} onClick={() => onSendMessage('My invoice has the wrong amount again')}>Invoice issue</button>
        <button className={styles.qb} onClick={() => onSendMessage('I still cannot log into my account')}>Login problem</button>
        <button className={styles.qb} onClick={() => onSendMessage('Where is my order ORD-789?')}>Track order</button>
        <button className={styles.qb} onClick={() => onSendMessage('I was charged twice this month')}>Double charge</button>
      </div>
      <div className={styles.inpRow}>
        <input 
          className={styles.inp} 
          placeholder="Message the agent..." 
          value={inputValue}
          onChange={e => onInputChange(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') onSendMessage(); }}
        />
        <button className={styles.sbtn} onClick={() => onSendMessage()}>&#10148;</button>
      </div>
    </div>
  );
}
