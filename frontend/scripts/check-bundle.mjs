#!/usr/bin/env node
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { gzipSync } from "node:zlib";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.join(root, "dist");
const manifestPath = path.join(dist, ".vite/manifest.json");
const budgetKb = Number(process.env.BUNDLE_BUDGET_KB ?? 200);

if (!Number.isFinite(budgetKb) || budgetKb <= 0) {
  console.error("BUNDLE_BUDGET_KB must be a positive number.");
  process.exit(1);
}
if (!existsSync(manifestPath)) {
  console.error("No Vite manifest found. Run `npm run build` before checking the bundle.");
  process.exit(1);
}

const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const entryKey = Object.keys(manifest).find((key) => manifest[key]?.isEntry);
if (!entryKey) {
  console.error("No entry chunk found in the Vite manifest.");
  process.exit(1);
}

const initialKeys = new Set();
function collectStaticImports(key) {
  if (initialKeys.has(key)) return;
  const chunk = manifest[key];
  if (!chunk) return;
  initialKeys.add(key);
  for (const imported of chunk.imports ?? []) collectStaticImports(imported);
}
collectStaticImports(entryKey);

let gzipBytes = 0;
const files = [];
for (const key of initialKeys) {
  const chunk = manifest[key];
  if (!chunk?.file?.endsWith(".js")) continue;
  const file = path.join(dist, chunk.file);
  const source = readFileSync(file);
  const bytes = gzipSync(source, { level: 9 }).length;
  gzipBytes += bytes;
  files.push({ file: chunk.file, bytes });
}

const gzipKb = gzipBytes / 1024;
const status = gzipKb <= budgetKb ? "OK" : "OVER BUDGET";
console.log(
  `Initial JavaScript: ${gzipKb.toFixed(1)} KB gzipped (budget ${budgetKb} KB) ${status}`,
);
for (const file of files) {
  console.log(`  ${(file.bytes / 1024).toFixed(1).padStart(6)} KB  ${file.file}`);
}
if (gzipKb > budgetKb) process.exit(1);
