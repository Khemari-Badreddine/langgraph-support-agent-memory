"use client";
import React from 'react';
import styles from './SupportAgentAppLayout.module.css';
import { Message } from './types';
import { TopBar } from './components/TopBar';
import { ChatPanel } from './components/ChatPanel';
import { MemoryPanel } from './components/MemoryPanel';
import { FlowPanel } from './components/FlowPanel';
import { UserSelector } from './components/UserSelector';
import { useFlow } from './hooks/useFlow';
import { useMemory } from './hooks/useMemory';
import { useChat } from './hooks/useChat';
import { useSession } from './hooks/useSession';

export function SupportAgentApp() {
  const flow = useFlow();
  const memory = useMemory();
  const chat = useChat(flow, memory);

  const session = useSession(
    () => {
      flow.resetFlow();
      memory.resetMemory();
      chat.resetChat();
    },
    (greeting: Message) => {
      chat.setMessages([greeting]);
    },
  );

  const sendMessage = (text: string = chat.inputValue) => {
    if (!session.currentUser) return;
    chat.sendMessage(text);
  };

  if (!session.currentUser) {
    return <UserSelector onConfirm={session.selectUser} />;
  }

  return (
    <div className={styles.root}>
      <TopBar
        currentUser={session.currentUser}
        sessionId={session.sessionId!}
        activeAgentBadge={flow.flow.activeAgentBadge}
        onNewConversation={session.newConversation}
        onSwitchUser={session.switchUser}
      />

      <div className={styles.body}>
        <FlowPanel flow={flow.flow} />

        <ChatPanel
          currentUser={session.currentUser}
          sessionCount={session.sessionCount}
          messages={chat.messages}
          isTyping={chat.isTyping}
          inputValue={chat.inputValue}
          onInputChange={chat.setInputValue}
          onSendMessage={sendMessage}
          openTraces={chat.openTraces}
          onToggleTrace={chat.toggleTrace}
          msgsEndRef={chat.msgsEndRef}
        />

        <MemoryPanel
          currentUser={session.currentUser}
          sessionId={session.sessionId!}
          sessionCount={session.sessionCount}
          live1={memory.live1}
          live2={memory.live2}
          addedIssues={memory.addedIssues}
          openPlus={memory.openPlus}
          dynMood={memory.dynMood}
        />
      </div>
    </div>
  );
}
