import { useState, useRef } from 'react';
import { Message, AgentRoute, TraceStep } from '../types';
import { API_BASE_URL, resultToRoute } from '../config';
import { now } from '../utils';
import { useFlow } from './useFlow';
import { useMemory } from './useMemory';

export function useChat(
  userId: string | null,
  sessionId: string | null,
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
    const traceMap = Object.fromEntries(result.trace.map(t => [t.step, t.detail]));
    const live1 = traceMap['memory'] || undefined;
    const specialistKeys = ['billing', 'tech', 'order', 'general'];
    const specStep = result.trace.find(t => specialistKeys.includes(t.step));
    const live2 = specStep?.detail || traceMap['triage'] || undefined;

    memory.applyMemoryUpdate({
      live: live1,
      live2: live2,
      openPlus: result.addIssue,
    });
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() || !userId || !sessionId) return;

    addUserMessage(text);
    showTypingAnimation();

    try {
      const res = await fetch(`${API_BASE_URL}/chat/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text.trim(),
          user_id: userId,
          session_id: sessionId,
        }),
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => null);
        throw new Error(errBody?.detail || `Request failed (${res.status})`);
      }

      const data = await res.json();
      const route = resultToRoute(data.result);

      setTimeout(() => {
        addAgentMessage(route);
        updateFlow(route);
        updateMemory(route);
        memory.refreshMemories();
      }, 400);
    } catch (err) {
      setIsTyping(false);
      const errorMsg: Message = {
        id: Date.now(),
        type: 'agent',
        text: err instanceof Error ? err.message : 'Something went wrong',
        time: now(),
        agentInfo: {
          cls: 'triageOnly',
          icon: '⬡',
          iconCls: 'none',
          specialist: 'Error',
          reply: 'Sorry, I encountered an error processing your request.',
          trace: [{ step: 'error', detail: err instanceof Error ? err.message : 'Unknown error' }],
          addIssue: false,
          openPlus: false,
        },
      };
      setMessages(prev => [...prev, errorMsg]);
    }
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