#!/usr/bin/env node
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import ts from "typescript";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const defaultFile = path.join(root, "src/copy.ts");

const banned = [
  ["rubric", /\brubrics?\b/gi],
  ["LLM", /\bllms?\b/gi],
  ["embedding", /\bembeddings?\b/gi],
  ["token", /\btokens?\b/gi],
  ["pipeline", /\bpipelines?\b/gi],
  ["JSON", /\bjson\b/gi],
  ["API", /\bapis?\b/gi],
  ["diarization", /\bdiarization\b/gi],
  ["kappa", /\bkappa\b/gi],
  ["latency", /\blatency\b/gi],
  ["inference", /\binference\b/gi],
  ["confidence", /\bconfidence\b/gi],
  ["evidence", /\bevidence\b/gi],
  ["unverified", /\bunverified\b/gi],
  ["workspace", /\bworkspaces?\b/gi],
  ["agent", /\bagents?\b/gi],
];

const args = process.argv.slice(2);
const fileIndex = args.indexOf("--file");
const target = path.resolve(
  fileIndex >= 0 && args[fileIndex + 1] ? args[fileIndex + 1] : defaultFile,
);

let source;
try {
  source = readFileSync(target, "utf8");
} catch {
  console.error(`Copy file not found: ${target}`);
  process.exit(1);
}

const sourceFile = ts.createSourceFile(
  target,
  source,
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TS,
);
const technicalRanges = [];

function collectTechnicalRanges(node) {
  if (
    ts.isVariableDeclaration(node) &&
    ts.isIdentifier(node.name) &&
    node.name.text === "technicalCopy" &&
    node.initializer
  ) {
    technicalRanges.push([node.initializer.getStart(sourceFile), node.initializer.getEnd()]);
  }
  ts.forEachChild(node, collectTechnicalRanges);
}
collectTechnicalRanges(sourceFile);

function insideTechnical(node) {
  const position = node.getStart(sourceFile);
  return technicalRanges.some(([start, end]) => position >= start && position < end);
}

const strings = [];
function collectStrings(node) {
  if (insideTechnical(node)) return;
  if (
    ts.isStringLiteral(node) ||
    ts.isNoSubstitutionTemplateLiteral(node) ||
    ts.isTemplateHead(node) ||
    ts.isTemplateMiddle(node) ||
    ts.isTemplateTail(node)
  ) {
    strings.push(node);
    return;
  }
  ts.forEachChild(node, collectStrings);
}
collectStrings(sourceFile);

const violations = [];
for (const node of strings) {
  for (const [label, pattern] of banned) {
    pattern.lastIndex = 0;
    if (!pattern.test(node.text)) continue;
    const { line, character } = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
    violations.push({
      label,
      line: line + 1,
      column: character + 1,
      text: node.text.replace(/\s+/g, " ").trim().slice(0, 100),
    });
  }
}

if (violations.length > 0) {
  console.error(`Banned words found in ${path.relative(process.cwd(), target)}:`);
  for (const violation of violations) {
    console.error(
      `  ${violation.line}:${violation.column}  ${violation.label}  "${violation.text}"`,
    );
  }
  process.exit(1);
}

console.log(`Copy check passed (${strings.length} strings checked).`);
