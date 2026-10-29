#!/usr/bin/env node
import { access, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import openapiTS, { astToString } from "openapi-typescript";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const source = path.resolve(root, "../backend/openapi.json");
const output = path.resolve(root, "src/api/schema.d.ts");
const banner = `/**
 * Generated from backend/openapi.json by \`npm run gen:api\`.
 * Do not edit by hand.
 */
`;

try {
  await access(source);
} catch {
  console.error(`API contract not found at ${source}`);
  process.exit(1);
}

const ast = await openapiTS(new URL(`file://${source}`));
const generated = astToString(ast);
if (!generated.includes("CallReport")) {
  console.error("The generated API types do not include CallReport.");
  process.exit(1);
}

await mkdir(path.dirname(output), { recursive: true });
await writeFile(
  output,
  `${banner}${generated.trimEnd()}

export type CallReport = components["schemas"]["CallReport"];
`,
  "utf8",
);
console.log(`Generated ${path.relative(root, output)} from ${path.relative(root, source)}.`);
