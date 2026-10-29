import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

type Tokens = Record<string, string>;

const css = readFileSync(path.resolve(process.cwd(), "src/theme/tokens.css"), "utf8");

function block(selector: string): Tokens {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = css.match(new RegExp(`${escaped}\\s*\\{([\\s\\S]*?)\\n\\}`));
  if (!match?.[1]) throw new Error(`Could not find token block ${selector}`);
  const tokens: Tokens = {};
  for (const item of match[1].matchAll(/--([\w-]+):\s*([^;]+);/g)) {
    if (item[1] && item[2] && !item[2].includes("\n")) {
      tokens[item[1]] = item[2].trim();
    }
  }
  return tokens;
}

function luminance(hex: string): number {
  const value = hex.replace("#", "");
  if (!/^[0-9a-f]{6}$/i.test(value)) throw new Error(`Expected a six-digit hex colour, got ${hex}`);
  const channels = [0, 2, 4].map(
    (offset) => Number.parseInt(value.slice(offset, offset + 2), 16) / 255,
  );
  const linear = channels.map((channel) =>
    channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4,
  );
  return 0.2126 * linear[0]! + 0.7152 * linear[1]! + 0.0722 * linear[2]!;
}

function ratio(foreground: string, background: string): number {
  const [high, low] = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (high! + 0.05) / (low! + 0.05);
}

function assertContrast(tokens: Tokens, foreground: string, background: string, minimum: number) {
  const fg = tokens[foreground];
  const bg = tokens[background];
  expect(fg, `missing token --${foreground}`).toBeTruthy();
  expect(bg, `missing token --${background}`).toBeTruthy();
  expect(
    ratio(fg!, bg!),
    `--${foreground} on --${background} should be at least ${minimum}:1`,
  ).toBeGreaterThanOrEqual(minimum);
}

const light = block(":root");
const dark = block(':root[data-theme="dark"]');
const systemDark = block(":root:not([data-theme])");

const textPairs = [
  ["ink", "paper", 7],
  ["ink", "surface", 7],
  ["muted", "paper", 4.5],
  ["muted", "surface", 4.5],
  ["on-primary", "primary", 7],
  ["status-done", "paper", 4.5],
  ["status-partly", "paper", 4.5],
  ["status-missed", "paper", 4.5],
  ["status-done", "surface", 4.5],
  ["status-partly", "surface", 4.5],
  ["status-missed", "surface", 4.5],
  ["highlight-ink", "highlight", 4.5],
] as const;

const markPairs = [
  ["rep", "paper", 3],
  ["customer", "paper", 3],
  ["rep", "surface", 3],
  ["customer", "surface", 3],
  ["focus", "paper", 3],
] as const;

describe("theme token contrast", () => {
  for (const [foreground, background, minimum] of textPairs) {
    it(`light text ${foreground} on ${background} meets ${minimum}:1`, () => {
      assertContrast(light, foreground, background, minimum);
    });
    it(`dark text ${foreground} on ${background} meets ${minimum}:1`, () => {
      assertContrast(dark, foreground, background, minimum);
    });
  }

  for (const [foreground, background, minimum] of markPairs) {
    it(`light mark ${foreground} on ${background} meets ${minimum}:1`, () => {
      assertContrast(light, foreground, background, minimum);
    });
    it(`dark mark ${foreground} on ${background} meets ${minimum}:1`, () => {
      assertContrast(dark, foreground, background, minimum);
    });
  }

  it("the system dark block matches the manual dark tokens", () => {
    for (const key of Object.keys(dark)) {
      if (key === "sans" || key === "measure") continue;
      expect(systemDark[key], `--${key} differs between system and manual dark`).toBe(dark[key]);
    }
  });
});
