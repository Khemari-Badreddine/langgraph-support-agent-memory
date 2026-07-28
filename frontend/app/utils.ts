export function genSessionId() {
  return 'sess_' + Math.random().toString(36).slice(2, 10);
}

export function now() {
  const d = new Date();
  return d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0');
}
