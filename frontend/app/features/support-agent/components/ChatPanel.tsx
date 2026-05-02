import type { RefObject } from "react";
import type { Message } from "../types";
import styles from "./ChatPanel.module.css";

interface ChatPanelProps {
  messages: Message[];
  isTyping: boolean;
  inputValue: string;
  quickQuestions: string[];
  messagesEndRef: RefObject<HTMLDivElement | null>;
  onInputChange: (value: string) => void;
  onSend: (text?: string) => void;
}

export function ChatPanel({
  messages,
  isTyping,
  inputValue,
  quickQuestions,
  messagesEndRef,
  onInputChange,
  onSend,
}: ChatPanelProps) {
  return (

    <div className={styles.chatPanel}>

      {/* // Chat header with avatar, customer name, and metadata */}
      <div className={styles.chatHead}>
        <div className={styles.avatar}>SC</div>
        <div className={styles.customerMeta}>
          <div className={styles.customerNameRow}>
            Sarah Chen
            <span className={styles.returningBadge}>RETURNING</span>
          </div>
          <div className={styles.customerSub}>3 past sessions - Last seen 2 days ago</div>
        </div>
      </div>
      {/* // Chat messages area with different styles for user and agent messages, and a typing indicator */}
      <div className={styles.messages}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            // Add different class for user and agent messages to style them differently
            className={`${styles.messageRow} ${msg.sender === "user" ? styles.messageRowUser : ""}`}>

            {/* Show agent marker for agent messages */}
            {msg.sender === "agent" && (
              <div className={styles.agentMarker}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="8" r="3" fill="#00E5A0" />
                  <path d="M6 20c0-4 2.7-6 6-6s6 2 6 6" stroke="#00E5A0" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
            )}

            {/*  Show message bubble with different styles for agent and user */}
            <div>
              <div className={`${styles.bubble} ${msg.sender === "agent" ? styles.bubbleAgent : styles.bubbleUser}`}>
                {/* If the message has HTML content, render it as HTML. Otherwise, render as plain text. */}
                {msg.html ? <div dangerouslySetInnerHTML={{ __html: msg.text }} /> : msg.text}
              </div>
              <div className={styles.timestamp}>{msg.timestamp}</div>
            </div>

          </div>
        ))}

        {isTyping && (
          <div className={styles.messageRow}>
            <div className={styles.agentMarker}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="8" r="3" fill="#00E5A0" />
              </svg>
            </div>
            <div className={styles.typingDots}>
              <span className={styles.typingDot} style={{ animationDelay: "0ms" }} />
              <span className={styles.typingDot} style={{ animationDelay: "180ms" }} />
              <span className={styles.typingDot} style={{ animationDelay: "360ms" }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {/* // Quick reply buttons that populate the input field with common questions when clicked */}
      <div className={styles.quickReplies}>
        {quickQuestions.map((question) => (
          <button key={question} onClick={() => onSend(question)} className={styles.quickReply}>
            {question}
          </button>
        ))}
      </div>
        {/* // Input area with text field and send button */}
      <div className={styles.inputRow}>
        <input
          type="text"
          value={inputValue}
          onChange={(event) => onInputChange(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && onSend()}
          placeholder="Message Sarah's agent..."
          className={styles.input}
        />
        <button onClick={() => onSend()} className={styles.sendButton}>
          {"->"}
        </button>
      </div>
    </div>
  );
}
