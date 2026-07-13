// src/mocks/rng.ts — Simple seeded random number generator for mock data.

let seed = 123456789;

export function resetSeed(newSeed: number) {
  seed = newSeed;
}

export function random() {
  const x = Math.sin(seed++) * 10000;
  return x - Math.floor(x);
}

export function int(min: number, max: number): number {
  return Math.floor(random() * (max - min + 1)) + min;
}

export function pick<T>(list: readonly T[]): T {
  return list[Math.floor(random() * list.length)];
}

export async function latency() {
  return new Promise((resolve) => setTimeout(resolve, int(50, 200)));
}
