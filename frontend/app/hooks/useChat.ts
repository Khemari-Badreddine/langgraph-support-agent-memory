import { useState, useRef } from 'react';
import { Message, AgentRoute } from '../types';
import { matchIntent } from '../config';
import { now } from '../utils';
import { useFlow } from './useFlow';
import { useMemory } from './useMemory';

export function useChat(
  flow: ReturnType<typeof useFlow>,
  memory: ReturnType<typeof useMemory>,
) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [openTraces, setOpenTraces] = useState<Record<number, boolean>>({});
  const msgsEndRef = useRef<HTMLDivElement>(null);

  const resetChat = () => {
    setMessages([]);
    setInputValue('');
    setIsTyping(false);
    setOpenTraces({});
  };

  const toggleTrace = (id: number) => {
    setOpenTraces(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const addUserMessage = (text: string) => {
    const userMsg: Message = { id: Date.now(), type: 'user', text: text.trim(), time: now() };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
  };

  const processMessage = (text: string): AgentRoute => {
    return matchIntent(text);
  };

  const showTypingAnimation = () => {
    setIsTyping(true);
    flow.startTriage();
    setTimeout(() => {
      flow.markTriageActive();
    }, 300);
  };

  const addAgentMessage = (result: AgentRoute) => {
    setIsTyping(false);
    setMessages(prev => {
      const agentMsg: Message = {
        id: Date.now(),
        type: 'agent',
        text: result.reply,
        time: now(),
        agentInfo: result,
      };
      return [...prev, agentMsg];
    });
  };

  const updateFlow = (result: AgentRoute) => {
    flow.completeFlow({
      specIcon: result.icon || '⬡',
      specIconCls: result.iconCls || 'none',
      specName: result.specialist,
      specDesc: result.cls === 'triageOnly' ? 'No route needed' : 'Query dispatched',
      activeAgentBadge: result.specialist + ' responded',
    });
  };

  const updateMemory = (result: AgentRoute) => {
    memory.applyMemoryUpdate({
      live: result.live ?? undefined,
      live2: result.live2 ?? undefined,
      addIssue: result.addIssue,
      specialistName: result.specialist,
      openPlus: result.openPlus,
    });
  };

  const sendMessage = (text: string) => {
    if (!text.trim()) return;

    addUserMessage(text);
    const result = processMessage(text);
    showTypingAnimation();

    setTimeout(() => {
      addAgentMessage(result);
      updateFlow(result);
      updateMemory(result);
    }, 1400);
  };

  return {
    messages,
    setMessages,
    inputValue,
    setInputValue,
    isTyping,
    openTraces,
    msgsEndRef,
    resetChat,
    toggleTrace,
    sendMessage,
  };
}
