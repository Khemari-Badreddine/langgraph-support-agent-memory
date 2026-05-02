import type { Issue, Message, Preference, ResponseRule, Stats } from "./types";

export const INITIAL_MESSAGES: Message[] = [
  {
    id: "1",
    text: "Hey Sarah 👋 Welcome back! I remember your previous conversations. How can I help you today?",
    sender: "agent",
    timestamp: "10:02 AM",
  },
];

export const INITIAL_ISSUES: Issue[] = [
  {
    id: "1",
    date: "Apr 20",
    status: "resolved",
    text: "Invoice <strong>#INV-123</strong> wrong amount - fixed $99->$89",
  },
  {
    id: "2",
    date: "Apr 22",
    status: "resolved",
    text: "<strong>Login timeout</strong> - password reset",
  },
];

export const INITIAL_PREFERENCES: Preference[] = [
  { id: "1", text: "Contact via <strong>Email</strong>" },
  { id: "2", text: "Language: <strong>English</strong>" },
];

export const INITIAL_STATS: Stats = {
  sessions: 4,
  openIssues: 1,
  sentiment: "Neutral",
  sentimentColor: "",
};

export const QUICK_QUESTIONS: string[] = [
  "My invoice has the wrong amount",
  "I cannot log in to my account",
  "Where is my order ORD-789?",
  "I was charged twice this month",
];

export const RESPONSE_RULES: ResponseRule[] = [
  {
    kw: ["invoice", "amount", "wrong", "charge", "bill"],
    msg: "I can see you had a billing issue on Apr 20 - invoice #INV-123 was corrected from $99 to $89. Is there a discrepancy on a new invoice? I'll look into it right now.",
    toast: "Memory saved: Invoice dispute opened",
    update: (data) => {
      data.setIssues((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          date: "Today",
          status: "new",
          text: "New invoice dispute opened",
        },
      ]);
      data.setStats((prev) => ({
        ...prev,
        openIssues: 2,
        sentiment: "Frustrated",
        sentimentColor: "coral",
      }));
    },
  },
  {
    kw: ["login", "log in", "password", "account", "sign", "access", "timeout"],
    msg: "You had a login timeout back on Apr 22 and we reset your password. Is this happening again? Given it's recurring, I'm escalating this right now.",
    toast: "Memory updated: Recurring login issue",
    update: (data) => {
      data.setIssues((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          date: "Today",
          status: "new",
          text: "Login issue - recurring",
        },
      ]);
      data.setStats((prev) => ({
        ...prev,
        sentiment: "Frustrated",
        sentimentColor: "coral",
      }));
    },
  },
  {
    kw: ["order", "track", "shipping", "delivery", "package", "where"],
    msg: "Your order <strong>ORD-789</strong> shipped Apr 24 via Express and is currently in transit. Estimated delivery today by 8 PM.",
    toast: "Memory saved: Tracking inquiry ORD-789",
    update: (data) => {
      data.setIssues((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          date: "Today",
          status: "resolved",
          text: "Order ORD-789 tracking query",
        },
      ]);
    },
  },
  {
    kw: ["twice", "double", "duplicate", "two charge"],
    msg: "I'm sorry about that - I can see a duplicate charge on your account. I'm flagging this for an immediate refund. You'll receive confirmation via email within 1-2 business days.",
    toast: "Memory saved: Duplicate charge -> refund initiated",
    update: (data) => {
      data.setIssues((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          date: "Today",
          status: "new",
          text: "Duplicate charge - refund pending",
        },
      ]);
      data.setStats((prev) => ({
        ...prev,
        openIssues: 2,
        sentiment: "Frustrated",
        sentimentColor: "coral",
      }));
    },
  },
];

export const FALLBACK_RULE: ResponseRule = {
  kw: [],
  msg: "Got it, Sarah. I have your full history here and I'm on it. Could you share a bit more detail so I can help as quickly as possible?",
  toast: null,
  update: () => {},
};
