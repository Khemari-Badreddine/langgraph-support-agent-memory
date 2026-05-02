import styles from "./TopBar.module.css";
import Image from "next/image";
import agentIcon from "../../../assets/csa_logo_icon.svg";
export function TopBar() {
  return (
    <div className={styles.topbar}>
      <div className={styles.brandRow}>
        <div className={styles.brandIcon}>
          <Image src={agentIcon} alt="Agent Icon" className={styles.brandIconImage} priority />
        </div>
        <div className={styles.brandCopy}>
          <span className={styles.brandEyebrow}>CUSTOMER SUPPORT</span>
          <span className={styles.brandName}>
            Agent
          </span>
          <span className={styles.brandUnderline} />
          <span className={styles.brandSubtext}>Memory-first customer intelligence</span>
        </div>
      </div>
      <div className={styles.sessionRow}>
        <div className={styles.liveDot} />
        <div className={styles.sessionPill}>user_123 - Session #4</div>
      </div>
    </div>
  );
}
