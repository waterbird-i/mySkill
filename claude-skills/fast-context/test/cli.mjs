#!/usr/bin/env node

import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import assert from "node:assert/strict";
import initSqlJs from "sql.js";

const scriptPath = resolve("scripts", "fast-context-search.mjs");
const tmpRoot = mkdtempSync(join(tmpdir(), "fast-context-skill-test-"));
const fakeKey = "sk-test-windsurf-key-1234567890";

function run(args) {
  return execFileSync(process.execPath, [scriptPath, ...args], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
}

try {
  const SQL = await initSqlJs();
  const db = new SQL.Database();
  const dbPath = join(tmpRoot, "state.vscdb");
  db.run("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)");
  db.run("INSERT INTO ItemTable (key, value) VALUES (?, ?)", [
    "windsurfAuthStatus",
    JSON.stringify({ apiKey: fakeKey }),
  ]);
  writeFileSync(dbPath, Buffer.from(db.export()));
  db.close();

  const checkOutput = run(["--check-key", "--db-path", dbPath]);
  assert.match(checkOutput, /Windsurf key discovered\./);
  assert.match(checkOutput, /Key: sk-test-.*567890/);
  assert.match(checkOutput, /Source: /);
  assert.doesNotMatch(checkOutput, new RegExp(fakeKey));

  const printOutput = run(["--print-key", "--db-path", dbPath]).trim();
  assert.equal(printOutput, fakeKey);

  const envOutput = run(["--key-env", "--db-path", dbPath]).trim();
  assert.equal(envOutput, `export WINDSURF_API_KEY='${fakeKey}'`);

  const conflict = spawnSync(
    process.execPath,
    [scriptPath, "--check-key", "--print-key", "--db-path", dbPath],
    { encoding: "utf8" }
  );
  assert.equal(conflict.status, 2);
  assert.match(conflict.stderr, /Choose only one key command/);
} finally {
  rmSync(tmpRoot, { recursive: true, force: true });
}
