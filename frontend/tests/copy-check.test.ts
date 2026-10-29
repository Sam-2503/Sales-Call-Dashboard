import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import { afterEach, describe, expect, it } from "vitest";

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const script = path.join(frontendRoot, "scripts/check-copy.mjs");
const temporaryDirectories: string[] = [];

function runCheck(args: string[] = []) {
  return spawnSync(process.execPath, [script, ...args], {
    cwd: frontendRoot,
    encoding: "utf8",
  });
}

function temporaryCopy(contents: string): string {
  const directory = mkdtempSync(path.join(tmpdir(), "call-review-copy-"));
  temporaryDirectories.push(directory);
  const file = path.join(directory, "copy.ts");
  writeFileSync(file, contents);
  return file;
}

afterEach(() => {
  for (const directory of temporaryDirectories.splice(0)) {
    rmSync(directory, { recursive: true, force: true });
  }
});

describe("copy guard", () => {
  it("passes the committed copy", () => {
    const result = runCheck();
    expect(result.status, result.stderr).toBe(0);
    expect(result.stdout).toContain("Copy check passed");
  });

  it("fails when a banned word is added", () => {
    const file = temporaryCopy('export const copy = { text: "This rubric is ready." };\n');
    const result = runCheck(["--file", file]);
    expect(result.status).toBe(1);
    expect(result.stderr).toContain("rubric");
  });

  it("allows technical terms inside the About this review block", () => {
    const file = temporaryCopy(
      'export const technicalCopy = { note: "The API and rubric are technical." };\nexport const copy = { text: "Plain words only." };\n',
    );
    const result = runCheck(["--file", file]);
    expect(result.status, result.stderr).toBe(0);
  });
});
