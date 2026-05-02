import type { ResponseRule } from '../app/features/support-agent/types';
import { RESPONSE_RULES, FALLBACK_RULE } from '../app/features/support-agent/config';
import { matchResponse } from '../app/features/support-agent/utils';
import { ChatOpenAI } from '@langchain/openai';
import { StateGraph, START, END } from '@langchain/langgraph';


type ProcessResult = {
    id: string;
    text: string;
    source: 'mock' | 'langgraph';
    toast?: string | null;
};

export async function processMessage(text: string): Promise<ProcessResult> {

    try {
       
        const apiKey = process.env.OPENAI_API_KEY;
        if (!apiKey) {
            throw new Error('OPENAI_API_KEY is required when LANGGRAPH_ENABLED=1');
        }

        // Minimal per-process memory (LangMem-style user context).
        const memory = getUserMemory('default');
        const model = new ChatOpenAI({ apiKey, model: process.env.OPENAI_MODEL ?? 'gpt-4o-mini', temperature: 0.2 });

        type GraphState = {
            userInput: string;
            memoryContext: string;
            reply: string;
        };

        const graph = new StateGraph<GraphState>({
            channels: {
                userInput: { value: (x: string, y: string) => y ?? x, default: () => '' },
                memoryContext: { value: (x: string, y: string) => y ?? x, default: () => '' },
                reply: { value: (x: string, y: string) => y ?? x, default: () => '' },
            },
        })
            .addNode('respond', async (state: GraphState) => {
                const prompt = [
                    'You are a customer support assistant.',
                    `User memory/context: ${state.memoryContext || 'none'}`,
                    `Customer message: ${state.userInput}`,
                    'Return a concise and empathetic support reply.',
                ].join('\n');

                const resp = await model.invoke(prompt);
                const out = typeof (resp as any).content === 'string' ? (resp as any).content : JSON.stringify((resp as any).content);
                return { reply: out };
            })
            .addEdge(START, 'respond')
            .addEdge('respond', END)
            .compile();

        const result = await graph.invoke({
            userInput: text,
            memoryContext: memory.join(' | ').slice(-1200),
            reply: '',
        });

        appendUserMemory('default', text);
        const replyText = typeof (result as any).reply === 'string' ? (result as any).reply : String((result as any).reply ?? '');
        return {
            id: Date.now().toString(),
            text: replyText,
            source: 'langgraph',
            toast: null,
        };
    } catch (err) {
        // Fall back to local rule engine on any failure
        // eslint-disable-next-line no-console
        console.warn('LangGraph integration failed, falling back to local rules', err);
    }


    // Local rule-based fallback (reuses client-side rules)
    const rule: ResponseRule = matchResponse(text, RESPONSE_RULES, FALLBACK_RULE);
    return {
        id: Date.now().toString(),
        text: rule.msg,
        source: 'mock',
        toast: rule.toast ?? null,
    };
}

export default processMessage;

const userMemoryStore = new Map<string, string[]>();

function getUserMemory(userId: string): string[] {
    return userMemoryStore.get(userId) ?? [];
}

function appendUserMemory(userId: string, value: string) {
    const current = getUserMemory(userId);
    const next = [...current, value].slice(-20);
    userMemoryStore.set(userId, next);
}
