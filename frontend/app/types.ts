// A customer issue stored in memory
export type Issue = {
  date: string;      // When the issue was created
  badge: string;     // Status (e.g. "open", "res")
  text: string;      // Description (may contain HTML)
};

// A stored customer preference
export type Pref = {
  text: string;      // e.g. "Prefers email communication"
};

// Customer profile
export type User = {
  id: string;              // Unique user ID
  name: string;            // Display name
  initials: string;        // Avatar initials
  tag: string;             // Internal tag (VIP, New, Returning...)
  tagLabel: string;        // Human-readable tag label
  color: string;           // Avatar/tag color
  sessions: number;        // Previous conversation count
  openIssues: number;      // Number of unresolved issues
  issues: Issue[];         // Stored customer issues
  prefs: Pref[];           // Stored customer preferences
  greeting: string;        // Initial greeting shown when chat starts
};

// One reasoning/trace step produced by an agent
export type TraceLine = {
  k: string;   // Trace type (thought, tool, action...)
  l: string;   // Trace description
};

// Output returned by the intent matcher/specialist
export type AgentRoute = {
  kw?: string[];          // Keywords that triggered this route
  specialist: string;     // Selected specialist agent
  cls: string;            // CSS class for the agent
  icon: string;           // Agent icon
  iconCls: string;        // Icon CSS class
  reply: string;          // Agent response
  trace: TraceLine[];     // Reasoning trace

  // Live toast notifications
  live?: string | null;
  live2?: string | null;

  // Memory updates
  addIssue: boolean;      // Whether to create a new issue
  openPlus: boolean;      // Increment open issue count
};

// A single chat message
export type Message = {
  id: number;                    // Unique message ID
  type: 'user' | 'agent';        // Sender
  text: string;                  // Message content
  time: string;                  // Timestamp
  agentInfo?: AgentRoute;        // Extra metadata for agent messages
};