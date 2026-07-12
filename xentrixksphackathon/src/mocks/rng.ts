// Seeded pseudo-random helpers for deterministic mock data.
let seed = 42;
function rand() {
  seed = (seed * 9301 + 49297) % 233280;
  return seed / 233280;
}
export function resetSeed(s = 42) {
  seed = s;
}
export function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(rand() * arr.length)];
}
export function int(min: number, max: number) {
  return Math.floor(rand() * (max - min + 1)) + min;
}
export function chance(p: number) {
  return rand() < p;
}
export function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
export function latency() {
  return sleep(300 + Math.random() * 500);
}
