import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const root = process.cwd();

describe("mock report fixtures", () => {
  it.each(["full_report.json", "insufficient_data_report.json"])(
    "keeps %s in sync with the shared fixture",
    (name) => {
      const source = readFileSync(path.join(root, "../fixtures/reports", name), "utf8");
      const copy = readFileSync(path.join(root, "src/mocks/fixtures", name), "utf8");
      expect(copy).toBe(source);
    },
  );
});
