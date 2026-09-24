import type { AgentEvent, Review } from '../types/agent';
export const API = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
let token = '';
export function setToken(value: string) { token = value; }
export function headers() { return { 'Content-Type': 'application/json', ...(token ? {Authorization: `Bearer ${token}`} : {}) }; }
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API}/api${path}`, { ...options, headers: headers() });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${response.status}). Check the repository URL and connection.`);
  }
  return response.json();
}
export const getReview = (id: string) => request<Review>(`/reviews/${encodeURIComponent(id)}`);

/** Fetch-based SSE supports bearer auth without putting secrets in URLs. Reconnect replays by ID. */
export async function streamEvents(id: string, after: number, signal: AbortSignal, receive: (e: AgentEvent) => void) {
  const response = await fetch(`${API}/api/reviews/${encodeURIComponent(id)}/events?after=${after}`, {headers: headers(), signal});
  if (!response.ok || !response.body) throw new Error(`Live connection failed (${response.status})`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, {stream:true}).replace(/\r\n/g, '\n');
      let split: number;
      while ((split = buffer.indexOf('\n\n')) >= 0) {
        const block = buffer.slice(0, split); buffer = buffer.slice(split + 2);
        if (block.includes('event: done')) return;
        const line = block.split('\n').find(l => l.startsWith('data: '));
        if (line) receive(JSON.parse(line.slice(6)));
      }
    }
  } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
}
