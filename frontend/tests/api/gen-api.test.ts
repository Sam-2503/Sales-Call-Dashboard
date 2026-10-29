import { spawnSync } from "node:child_process";
import { copyFileSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { afterEach, describe, expect, it } from "vitest";

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const script = path.join(frontendRoot, "scripts/gen-api.mjs");
const schema = path.join(frontendRoot, "src/api/schema.d.ts");
const directories: string[] = [];

function run(args: string[]) {
  return spawnSync(process.execPath, [script, ...args], {
    cwd: frontendRoot,
    encoding: "utf8",
  });
}

function temporaryDirectory(): string {
  const directory = mkdtempSync(path.join(tmpdir(), "call-review-api-"));
  directories.push(directory);
  return directory;
}

afterEach(() => {
  for (const directory of directories.splice(0)) {
    rmSync(directory, { recursive: true, force: true });
  }
});

describe("generated API types", () => {
  it("matches the committed schema", () => {
    const result = run(["--check"]);
    expect(result.status, result.stderr).toBe(0);
    expect(result.stdout).toContain("API types are up to date");
  });

  it("fails when the contract changes without regeneration", () => {
    const directory = temporaryDirectory();
    const source = path.join(directory, "openapi.json");
    const output = path.join(directory, "schema.d.ts");
    const spec = JSON.parse(
      readFileSync(path.join(frontendRoot, "../backend/openapi.json"), "utf8"),
    ) as { components: { schemas: Record<string, unknown> } };
    spec.components.schemas.DriftProbe = {
      type: "object",
      properties: { value: { type: "string" } },
      required: ["value"],
    };
    writeFileSync(source, JSON.stringify(spec));
    copyFileSync(schema, output);

    const result = run(["--check", "--source", source, "--output", output]);
    expect(result.status).toBe(1);
    expect(result.stderr).toContain("out of date");
  });
});
