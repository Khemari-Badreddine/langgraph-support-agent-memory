import { User, AgentRoute } from './types';

export const USERS: User[] = [
  {
    id: 'user_123',
    name: 'Sarah Chen',
    initials: 'SC',
    tag: 'ret',
    tagLabel: 'Returning',
    color: 'linear-gradient(135deg,#FF6B4A,#FF9B7A)',
    sessions: 4,
    openIssues: 1,
    issues: [
      { date: 'Apr 20', badge: 'res', text: 'Invoice <strong>#INV-123</strong> wrong amount' },
      { date: 'Apr 22', badge: 'res', text: '<strong>Login timeout</strong> — pw reset' },
    ],
    prefs: [
      { text: 'Contact via <strong>Email</strong>' },
      { text: 'Language: <strong>English</strong>' },
    ],
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
      { k: 'thought', l: 'Intent classified as billing_dispute (conf: 0.94)' },
      { k: 'tool', l: 'lookup_invoices(user_id)' },
      { k: 'result', l: 'Found duplicate charge — possible billing error' },
      { k: 'memory', l: 'Stored: "Invoice dispute opened today"' },
      { k: 'action', l: 'Suggested refund + flagged for review' },
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
      { k: 'thought', l: 'Intent classified as auth_failure / recurring (conf: 0.91)' },
      { k: 'tool', l: 'search_memory(user_id, "login")' },
      { k: 'result', l: 'Previous login issue found in memory' },
      { k: 'memory', l: 'Updated: "Login issue marked recurring"' },
      { k: 'action', l: 'Escalated to Tier-2 tech team' },
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
      { k: 'thought', l: 'Intent classified as order_tracking (conf: 0.97)' },
      { k: 'tool', l: 'fetch_order_status(order_id)' },
      { k: 'result', l: 'Status: IN_TRANSIT · Carrier: FedEx · ETA: today' },
      { k: 'memory', l: 'Stored: "Tracking inquiry logged"' },
      { k: 'action', l: 'Returned live ETA to customer' },
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
      { k: 'thought', l: 'Intent unclear — requesting clarification' },
      { k: 'memory', l: 'Searched memory — no matching prior issue' },
      { k: 'action', l: 'Returning to customer for more detail' },
    ],
    live: null,
    live2: null,
    addIssue: false,
    openPlus: false,
  }
};

export function matchIntent(t: string): AgentRoute {
  const l = t.toLowerCase();
  for (const [k, r] of Object.entries(DB)) {
    if (k === 'fallback') continue;
    if (r.kw && r.kw.some(w => l.includes(w))) return r;
  }
  return DB.fallback;
}
