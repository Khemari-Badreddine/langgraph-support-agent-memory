import { useState } from 'react';

export interface FlowState {
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
  activeAgentBadge: string;
}

const INITIAL_FLOW: FlowState = {
  triage: false,
  specialist: false,
  respond: false,
  specIcon: '—',
  specIconCls: 'none',
  specName: 'Specialist',
  specDesc: 'Awaiting route',
  respIcon: '—',
  respIconCls: 'none',
  respDesc: 'Pending',
  activeAgentBadge: 'Triage ready',
};

export function useFlow() {
  const [flow, setFlow] = useState<FlowState>(INITIAL_FLOW);

  const resetFlow = () => setFlow(INITIAL_FLOW);

  const startTriage = () =>
    setFlow(prev => ({ ...prev, triage: false, specialist: false, respond: false }));

  const markTriageActive = () =>
    setFlow(prev => ({ ...prev, triage: true }));

  const completeFlow = (params: {
    specIcon: string;
    specIconCls: string;
    specName: string;
    specDesc: string;
    activeAgentBadge: string;
  }) =>
    setFlow({
      triage: true,
      specialist: true,
      respond: true,
      specIcon: params.specIcon,
      specIconCls: params.specIconCls,
      specName: params.specName,
      specDesc: params.specDesc,
      respIcon: '✓',
      respIconCls: 'billing',
      respDesc: 'Sent to customer',
      activeAgentBadge: params.activeAgentBadge,
    });

  return { flow, resetFlow, startTriage, markTriageActive, completeFlow };
}
