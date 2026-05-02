"use client";

import { useEffect, useRef, useState } from "react";
import {
  FALLBACK_RULE,
  INITIAL_ISSUES,
  INITIAL_MESSAGES,
  INITIAL_PREFERENCES,
  INITIAL_STATS,
  QUICK_QUESTIONS,
  RESPONSE_RULES,
} from "./config";

import { formatTime, matchResponse } from "./utils";
import type { Issue, Message, Stats } from "./types";
import styles from "./SupportAgentAppLayout.module.css";
import { ChatPanel } from "./components/ChatPanel";
import { MemoryPanel } from "./components/MemoryPanel";
import { Toast } from "./components/Toast";
import { TopBar } from "./components/TopBar";

export function SupportAgentApp() {
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [issues, setIssues] = useState<Issue[]>(INITIAL_ISSUES);
  const [stats, setStats] = useState<Stats>(INITIAL_STATS);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const showToast = (message: string) => {
    setToast(message);
    setTimeout(() => setToast(null), 2800);
  };

  const handleSend = (text?: string) => {
    const content = text ?? inputValue.trim();
    if (!content) return;

    setInputValue("");

    const userMsg: Message = {
      id: Date.now().toString(),
      text: content,
      sender: "user",
      timestamp: formatTime(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    const response = matchResponse(content, RESPONSE_RULES, FALLBACK_RULE);

    setTimeout(() => {
      setIsTyping(false);

      const agentMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: response.msg,
        sender: "agent",
        timestamp: formatTime(),
        html: true,
      };

      setMessages((prev) => [...prev, agentMsg]);

      if (response.toast) {
        showToast(response.toast);
      }

      response.update({ setIssues, setStats });
    }, 1200);
  };

  return (
    <div className={styles.root}>
      <div className={styles.shell}>
        <TopBar />

        <div className={styles.content}>
          <ChatPanel
            messages={messages}
            isTyping={isTyping}
            inputValue={inputValue}
            quickQuestions={QUICK_QUESTIONS}
            messagesEndRef={messagesEndRef}
            onInputChange={setInputValue}
            onSend={handleSend}
          />

          <MemoryPanel
            issues={issues}
            preferences={INITIAL_PREFERENCES}
            stats={stats}
          />
        </div>
      </div>

      {toast && <Toast message={toast} />}
    </div>
  );
}
