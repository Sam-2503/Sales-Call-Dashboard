#!/usr/bin/env node
import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.join(root, "dist");
const textExtensions = new Set([".html", ".js", ".css", ".svg", ".json", ".txt", ".xml"]);
const allowed = new Set([
  "http://www.w3.org/2000/svg",
  "http://www.w3.org/1999/xlink",
  "http://www.w3.org/1999/xhtml",
  "http://www.w3.org/1998/Math/MathML",
  "http://www.w3.org/XML/1998/namespace",
]);
// React includes its error-decoder link as a static string in the production
// build, and MSW's worker carries its project link in a comment. Neither is
// fetched, so neither is a runtime request.
const allowedPrefixes = ["https://react.dev/errors/", "https://github.com/mswjs/msw"];
const urlPattern = /https?:\/\/[^\s"'<>`)\\]+/gi;

if (!existsSync(dist)) {
  console.error("No dist directory. Run `npm run build` before checking external requests.");
  process.exit(1);
}

function walk(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(directory, entry.name);
    return entry.isDirectory() ? walk(full) : [full];
  });
}

const violations = [];
for (const file of walk(dist)) {
  if (!textExtensions.has(path.extname(file))) continue;
  const text = readFileSync(file, "utf8");
  for (const match of text.matchAll(urlPattern)) {
    const url = match[0].replace(/[.,;:]+$/, "");
    if (!allowed.has(url) && !allowedPrefixes.some((prefix) => url.startsWith(prefix))) {
      violations.push({ file: path.relative(root, file), url });
    }
  }
}

if (violations.length > 0) {
  console.error("The build contains URLs to other origins:");
  for (const violation of violations.slice(0, 30)) {
    console.error(`  ${violation.file}: ${violation.url}`);
  }
  if (violations.length > 30) {
    console.error(`  ...and ${violations.length - 30} more.`);
  }
  process.exit(1);
}

console.log("No external URLs found in the build (namespace strings are allowed).");
