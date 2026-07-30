import { User, AgentRoute, TraceStep } from './types';

export const API_BASE_URL = 'http://localhost:8000';

export function backendTraceToTraceLine(trace: TraceStep[]) {
  return trace;
}

const INTENT_MAP: Record<string, { cls: string; icon: string; iconCls: string }> = {
  billing: { cls: 'billing', icon: '$', iconCls: 'billing' },
  tech:    { cls: 'tech',   icon: '⚙', iconCls: 'tech' },
  order:   { cls: 'order',  icon: '📦',iconCls: 'order' },
};

export function resultToRoute(result: {
  id: string;
  text: string;
  intent: string;
  specialist: string;
  trace: TraceStep[];
  memories_updated: boolean;
}): AgentRoute {
  const mapped = INTENT_MAP[result.intent] || { cls: 'triageOnly', icon: '⬡', iconCls: 'none' };
  return {
    ...mapped,
    specialist: result.specialist,
    reply: result.text,
    trace: backendTraceToTraceLine(result.trace),
    addIssue: result.memories_updated,
    openPlus: result.memories_updated,
  };
}

export const USERS: User[] = [
  {
    id: 'user_123',
    name: 'Sarah Chen',
    initials: 'SC',
    tag: 'ret',
    tagLabel: 'Returning',
    color: 'linear-gradient(135deg,#FF6B4A,#FF9B7A)',
    sessions: 4,
    openIssues: 0,
    issues: [],
    prefs: [],
    greeting: "Hey Sarah 👋 Welcome back! I have your full history here. What can I help you with today?",
  },
  {
    id: 'user_456',
    name: 'James Okafor',
    initials: 'JO',
    tag: 'new',
    tagLabel: 'New',
    color: 'linear-gradient(135deg,#60A5FA,#93C5FD)',
    sessions: 1,
    openIssues: 0,
    issues: [
      { date: 'Apr 18', badge: 'res', text: 'Order <strong>ORD-789</strong> not delivered — reshipped' },
    ],
    prefs: [
      { text: 'Contact via <strong>SMS</strong>' },
    ],
    greeting: "Hi James! Good to have you back. How can I help you today?",
  },
  {
    id: 'user_789',
    name: 'Priya Sharma',
    initials: 'PS',
    tag: 'new',
    tagLabel: 'New',
    color: 'linear-gradient(135deg,#A78BFA,#C4B5FD)',
    sessions: 0,
    openIssues: 0,
    issues: [],
    prefs: [],
    greeting: "Hi Priya! I'm your support agent. What can I help you with today?",
  },
];

export const DB: Record<string, AgentRoute> = {
  billing: {
    kw: ['invoice', 'amount', 'wrong', 'charge', 'bill', 'twice', 'double', 'refund', 'duplicate'],
    specialist: 'Billing',
    cls: 'billing',
    icon: '$',
    iconCls: 'billing',
    reply: "I can see you had a billing issue before. I'm pulling up your recent transactions now — I'll have this resolved immediately.",
    trace: [
      { step: 'thought', detail: 'Intent classified as billing_dispute (conf: 0.94)' },
      { step: 'tool', detail: 'lookup_invoices(user_id)' },
      { step: 'result', detail: 'Found duplicate charge — possible billing error' },
      { step: 'memory', detail: 'Stored: "Invoice dispute opened today"' },
      { step: 'action', detail: 'Suggested refund + flagged for review' },
    ],
    live: 'New issue: Invoice dispute opened',
    live2: 'Sentiment updated → Frustrated',
    addIssue: true,
    openPlus: true,
  },
  tech: {
    kw: ['login', 'log in', 'password', 'account', 'sign', 'access', 'timeout', 'cannot'],
    specialist: 'Tech Support',
    cls: 'tech',
    icon: '⚙',
    iconCls: 'tech',
    reply: "I can see your tech history. Since this appears to be recurring, I'm escalating immediately and flagging this as a persistent auth issue.",
    trace: [
      { step: 'thought', detail: 'Intent classified as auth_failure / recurring (conf: 0.91)' },
      { step: 'tool', detail: 'search_memory(user_id, "login")' },
      { step: 'result', detail: 'Previous login issue found in memory' },
      { step: 'memory', detail: 'Updated: "Login issue marked recurring"' },
      { step: 'action', detail: 'Escalated to Tier-2 tech team' },
    ],
    live: 'Login issue flagged as recurring',
    live2: 'Ticket escalated to Tier-2',
    addIssue: true,
    openPlus: true,
  },
  order: {
    kw: ['order', 'track', 'shipping', 'delivery', 'package', 'where', 'ord'],
    specialist: 'Order Tracking',
    cls: 'order',
    icon: '📦',
    iconCls: 'order',
    reply: "Let me check on that order. It shipped recently via Express and is currently in transit — estimated delivery by end of day.",
    trace: [
      { step: 'thought', detail: 'Intent classified as order_tracking (conf: 0.97)' },
      { step: 'tool', detail: 'fetch_order_status(order_id)' },
      { step: 'result', detail: 'Status: IN_TRANSIT · Carrier: FedEx · ETA: today' },
      { step: 'memory', detail: 'Stored: "Tracking inquiry logged"' },
      { step: 'action', detail: 'Returned live ETA to customer' },
    ],
    live: 'Tracking query logged',
    live2: null,
    addIssue: false,
    openPlus: false,
  },
  fallback: {
    specialist: 'Triage',
    cls: 'triageOnly',
    icon: '⬡',
    iconCls: 'none',
    reply: "Got it. I have your full history here and I'm ready to help. Could you share a few more details so I can route this to the right specialist?",
    trace: [
      { step: 'thought', detail: 'Intent unclear — requesting clarification' },
      { step: 'memory', detail: 'Searched memory — no matching prior issue' },
      { step: 'action', detail: 'Returning to customer for more detail' },
    ],
    live: null,
    live2: null,
    addIssue: false,
    openPlus: false,
  }
};

export function matchIntent(t: string): AgentRoute {
  const detail = t.toLowerCase();
  for (const [step, r] of Object.entries(DB)) {
    if (step === 'fallback') continue;
    if (r.kw && r.kw.some(w => detail.includes(w))) return r;
  }
  return DB.fallback;
}
