import { useState } from 'react';
import { User, Message } from '../types';
import { genSessionId, now } from '../utils';

export function useSession(
  onSessionReset: () => void,
  onGreeting: (msg: Message) => void,
) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionCount, setSessionCount] = useState(0);

  const selectUser = (u: User) => {
    const sId = genSessionId();
    const sCount = (u.sessions || 0) + 1;
    setCurrentUser(u);
    setSessionId(sId);
    setSessionCount(sCount);
    onSessionReset();

    onGreeting({
      id: Date.now(),
      type: 'agent',
      text: u.greeting,
      time: now(),
      agentInfo: {
        cls: 'triageOnly',
        icon: '⬡',
        iconCls: 'none',
        specialist: 'Triage',
        reply: u.greeting,
        trace: [{ step: 'thought', detail: 'Session started — memory loaded' }],
        addIssue: false,
        openPlus: false,
      },
    });
  };

  const newConversation = () => {
    if (!currentUser) return;
    setSessionId(genSessionId());
    setSessionCount(prev => prev + 1);
    onSessionReset();
  };

  const switchUser = () => {
    setCurrentUser(null);
    setSessionId(null);
  };

  return {
    currentUser,
    sessionId,
    sessionCount,
    selectUser,
    newConversation,
    switchUser,
  };
}
