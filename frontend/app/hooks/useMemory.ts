import { useState, useEffect, useRef } from 'react';
import { Issue } from '../types';
import { API_BASE_URL } from '../config';

export interface DynMood {
  mood: string;
  cls: string;
}

export function useMemory(userId: string | null) {
  const [live1, setLive1] = useState<string | null>(null);
  const [live2, setLive2] = useState<string | null>(null);
  const [openPlus, setOpenPlus] = useState(0);
  const [dynMood, setDynMood] = useState<DynMood | null>(null);
  const [backendIssues, setBackendIssues] = useState<Issue[]>([]);
  const prevUserId = useRef<string | null>(null);

  useEffect(() => {
    if (!userId) {
      setBackendIssues([]);
      prevUserId.current = null;
      return;
    }
    if (userId === prevUserId.current) return;
    prevUserId.current = userId;
    fetchMemories();
  }, [userId]);

  const fetchMemories = () => {
    if (!userId) return;
    fetch(`${API_BASE_URL}/memory/${userId}`)
      .then(res => res.ok ? res.json() : { memories: [] })
      .then(data => setBackendIssues(data.memories || []))
      .catch(() => setBackendIssues([]));
  };

  const clearMemory = async () => {
    if (!userId) return;
    try {
      await fetch(`${API_BASE_URL}/memory/${userId}`, { method: 'DELETE' });
    } catch {
      // ignore
    }
    setBackendIssues([]);
  };

  const refreshMemories = () => {
    fetchMemories();
  };

  const resetMemory = () => {
    setLive1(null);
    setLive2(null);
    setOpenPlus(0);
    setDynMood(null);
  };

  const applyMemoryUpdate = (params: {
    live?: string;
    live2?: string;
    openPlus?: boolean;
    mood?: string;
    moodCls?: string;
  }) => {
    if (params.live) {
      setLive1(params.live);
      setTimeout(() => setLive1(null), 4000);
    }
    if (params.live2) {
      setTimeout(() => {
        setLive2(params.live2 || null);
        setTimeout(() => setLive2(null), 4000);
      }, 700);
    }
    if (params.openPlus) setOpenPlus(prev => prev + 1);
    if (params.mood) setDynMood({ mood: params.mood, cls: params.moodCls || '' });
  };

  return { live1, live2, openPlus, dynMood, backendIssues, resetMemory, applyMemoryUpdate, clearMemory, refreshMemories };
}