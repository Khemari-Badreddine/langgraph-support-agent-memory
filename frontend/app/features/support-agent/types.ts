import type { Dispatch, SetStateAction } from "react";

export type Sender = "user" | "agent";

export interface Message {
  id: string;
  text: string;
  sender: Sender;
  timestamp: string;
  html?: boolean;
}

export type IssueStatus = "resolved" | "open" | "new";

export interface Issue {
  id: string;
  date: string;
  status: IssueStatus;
  text: string;
}

export interface Preference {
  id: string;
  text: string;
}

export type SentimentTone = "teal" | "coral" | "amber" | "";

export interface Stats {
  sessions: number;
  openIssues: number;
  sentiment: string;
  sentimentColor: SentimentTone;
}

export interface ResponseUpdateContext {
  setIssues: Dispatch<SetStateAction<Issue[]>>;
  setStats: Dispatch<SetStateAction<Stats>>;
}

export interface ResponseRule {
  kw: string[];
  msg: string;
  toast: string | null;
  update: (data: ResponseUpdateContext) => void;
}
