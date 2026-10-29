#!/usr/bin/env node
import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import openapiTS, { astToString } from "openapi-typescript";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const checkOnly = args.includes("--check");

function argument(name) {
  const index = args.indexOf(name);
  return index >= 0 && args[index + 1] ? path.resolve(process.cwd(), args[index + 1]) : undefined;
}

const source = argument("--source") ?? path.resolve(root, "../backend/openapi.json");
const output = argument("--output") ?? path.resolve(root, "src/api/schema.d.ts");
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

const ast = await openapiTS(pathToFileURL(source));
const generated = astToString(ast);
if (!generated.includes("CallReport")) {
  console.error("The generated API types do not include CallReport.");
  process.exit(1);
}

const content = `${banner}${generated.trimEnd()}

export type CallReport = components["schemas"]["CallReport"];
`;

if (checkOnly) {
  let current;
  try {
    current = await readFile(output, "utf8");
  } catch {
    console.error(`Generated API types are missing at ${output}. Run npm run gen:api.`);
    process.exit(1);
  }
  if (current !== content) {
    console.error(`Generated API types are out of date at ${output}. Run npm run gen:api.`);
    process.exit(1);
  }
  console.log(`API types are up to date (${path.relative(root, output)}).`);
} else {
  await mkdir(path.dirname(output), { recursive: true });
  await writeFile(output, content, "utf8");
  console.log(`Generated ${path.relative(root, output)} from ${path.relative(root, source)}.`);
}
