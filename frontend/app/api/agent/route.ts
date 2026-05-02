import { NextRequest, NextResponse } from 'next/server';
import processMessage from '../../../server/agent';

const BACKEND_URL = process.env.AGENT_BACKEND_URL;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const text = body?.text ?? '';
    if (!text || typeof text !== 'string') {
      return NextResponse.json({ error: 'Missing `text` in request body' }, { status: 400 });
    }

    // If an external FastAPI backend is configured, proxy the request to it.
    if (BACKEND_URL) {
      try {
        const res = await fetch(new URL('/agent/respond', BACKEND_URL).toString(), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, user_id: body?.user_id ?? 'default', session_id: body?.session_id ?? '' }),
        });
        const json = await res.json();
        return NextResponse.json(json, { status: res.status });
      } catch (err) {
        // eslint-disable-next-line no-console
        console.warn('Failed to proxy to external AGENT_BACKEND_URL, falling back to local processor', err);
      }
    }

    const result = await processMessage(text);
    return NextResponse.json({ ok: true, result });
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('agent route error', err);
    return NextResponse.json({ error: 'internal' }, { status: 500 });
  }
}
