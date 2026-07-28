import React from 'react';
import styles from './FlowPanel.module.css';

interface FlowState {
  triage: boolean;
  specialist: boolean;
  respond: boolean;
  specIcon: string;
  specIconCls: string;
  specName: string;
  specDesc: string;
  respIcon: string;
  respIconCls: string;
  respDesc: string;
}

interface FlowPanelProps {
  flow: FlowState;
}

function getSpecIconClass(cls: string, s: typeof styles): string {
  if (cls === 'billing') return s.flowIconBilling;
  if (cls === 'tech') return s.flowIconTech;
  if (cls === 'order') return s.flowIconOrder;
  return s.flowIconNone;
}

export function FlowPanel({ flow }: FlowPanelProps) {
  return (
    <div className={styles.flow}>
    
      <div className={styles.flowHead}>
        <div className={styles.panelLabel}>Agent Flow</div>
      </div>
      
      <div className={styles.flowBody}>

        {/* Triage Step */}
        <div className={`${styles.flowStep} ${flow.triage ? styles.flowStepActive : ''}`}>
          <div className={`${styles.flowIcon} ${styles.flowIconTriage}`}>⬡</div>
          <div className={styles.flowTxt}>
            <div className={styles.flowName}>Triage</div>
            <div className={styles.flowDesc}>Classifies intent</div>
          </div>
        </div>

        <div className={styles.flowConnector}></div>

        {/* Specialist Step */}
        <div className={`${styles.flowStep} ${flow.specialist ? styles.flowStepActive : ''}`}>
          <div className={`${styles.flowIcon} ${getSpecIconClass(flow.specIconCls, styles)}`}>
            {flow.specIcon}
          </div>
          <div className={styles.flowTxt}>
            <div className={styles.flowName}>{flow.specName}</div>
            <div className={styles.flowDesc}>{flow.specDesc}</div>
          </div>
        </div>

        <div className={styles.flowConnector}></div>

        {/* Response Step */}
        <div className={`${styles.flowStep} ${flow.respond ? styles.flowStepActive : ''}`}>
          <div className={`${styles.flowIcon} ${flow.respIconCls === 'billing' ? styles.flowIconBilling : styles.flowIconNone}`}>
            {flow.respIcon}
          </div>
          <div className={styles.flowTxt}>
            <div className={styles.flowName}>Response</div>
            <div className={styles.flowDesc}>{flow.respDesc}</div>
          </div>
        </div>

      </div>
    </div>
  );
}
