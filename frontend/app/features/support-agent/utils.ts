import type { ResponseRule } from "./types";

export function formatTime(): string {
  const now = new Date();
  const hours = now.getHours().toString().padStart(2, "0");
  const minutes = now.getMinutes().toString().padStart(2, "0");
  return `${hours}:${minutes}`;
}

export function matchResponse(text: string, rules: ResponseRule[], fallbackRule: ResponseRule): ResponseRule {
  const lower = text.toLowerCase();
  for (const rule of rules) {
    if (rule.kw.some((keyword) => lower.includes(keyword))) {
      return rule;
    }
  }
  return fallbackRule;
}

export function getStatusBadgeColor(status: "resolved" | "open" | "new") {
  if (status === "resolved") return "statusResolved";
  if (status === "new") return "statusNew";
  return "statusOpen";
}

export function getSentimentColor(sentimentColor: "teal" | "coral" | "amber" | "") {
  if (sentimentColor === "coral") return "sentimentCoral";
  if (sentimentColor === "amber") return "sentimentAmber";
  return "sentimentDefault";
}
