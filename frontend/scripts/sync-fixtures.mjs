#!/usr/bin/env node
import { copyFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const source = path.resolve(root, "../fixtures/reports");
const destination = path.resolve(root, "src/mocks/fixtures");
const files = ["full_report.json", "insufficient_data_report.json"];

await mkdir(destination, { recursive: true });
for (const file of files) {
  await copyFile(path.join(source, file), path.join(destination, file));
  console.log(`Synced ${path.relative(root, path.join(destination, file))}`);
}
