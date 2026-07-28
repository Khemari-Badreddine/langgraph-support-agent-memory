import { useState } from 'react';

export interface AddedIssue {
  id: number;
  text: string;
  date: string;
  flash: boolean;
}

export interface DynMood {
  mood: string;
  cls: string;
}

export function useMemory() {
  const [live1, setLive1] = useState<string | null>(null);
  const [live2, setLive2] = useState<string | null>(null);
  const [addedIssues, setAddedIssues] = useState<AddedIssue[]>([]);
  const [openPlus, setOpenPlus] = useState(0);
  const [dynMood, setDynMood] = useState<DynMood | null>(null);

  const resetMemory = () => {
    setLive1(null);
    setLive2(null);
    setAddedIssues([]);
    setOpenPlus(0);
    setDynMood(null);
  };

  const applyMemoryUpdate = (params: {
    live?: string;
    live2?: string;
    addIssue?: boolean;
    specialistName?: string;
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
    if (params.addIssue) {
      const issueId = Date.now();
      setAddedIssues(prev => [
        ...prev,
        { text: `${params.specialistName} issue logged`, date: 'Today', flash: true, id: issueId },
      ]);
      setTimeout(() => {
        setAddedIssues(prev =>
          prev.map(i => (i.id === issueId ? { ...i, flash: false } : i))
        );
      }, 1500);
    }
    if (params.openPlus) setOpenPlus(prev => prev + 1);
    if (params.mood) setDynMood({ mood: params.mood, cls: params.moodCls || '' });
  };

  return { live1, live2, addedIssues, openPlus, dynMood, resetMemory, applyMemoryUpdate };
}
