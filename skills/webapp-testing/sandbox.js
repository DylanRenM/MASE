/**
 * E2E Sandbox — containment-safe snapshot, restore, and verification.
 *
 * All configured filesystem paths are project-relative, canonicalized, and
 * constrained by safety.allowed_roots before they are read or mutated.
 */

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const WINDOWS_ABSOLUTE = /^(?:[A-Za-z]:[\\/]|\\\\)/;

let _snapshotData = null;
let _config = null;
let _snapshotPath = null;
let _projectRoot = null;
let _allowedRoots = [];
let _neverBackup = [];

function loadConfig() {
  const configPath = path.resolve(process.cwd(), 'sandbox.config.json');
  if (!fs.existsSync(configPath)) {
    console.warn('[sandbox] sandbox.config.json 未找到，使用默认空配置（仅监控 .env）');
    return {
      snapshot: { directories: [], files: ['.env'], env_vars: [] },
      validation: { strict: true },
      safety: { allowed_roots: ['.'], never_backup: [] }
    };
  }
  return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
}

function relativeParts(value) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error('[sandbox] 路径必须是非空项目相对路径');
  }
  if (path.isAbsolute(value) || WINDOWS_ABSOLUTE.test(value)) {
    throw new Error(`[sandbox] 拒绝绝对路径: ${value}`);
  }
  const parts = value.replaceAll('\\', '/').split('/');
  if (parts.includes('..')) {
    throw new Error(`[sandbox] 拒绝路径穿越: ${value}`);
  }
  return parts.filter(part => part && part !== '.');
}

function isWithin(candidate, root) {
  const relative = path.relative(root, candidate);
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}

function canonicalizeCandidate(candidate) {
  let cursor = candidate;
  const suffix = [];
  while (!fs.existsSync(cursor)) {
    const parent = path.dirname(cursor);
    if (parent === cursor) break;
    suffix.unshift(path.basename(cursor));
    cursor = parent;
  }
  const canonicalParent = fs.realpathSync.native(cursor);
  return path.join(canonicalParent, ...suffix);
}

function projectRelative(value) {
  const parts = relativeParts(value);
  const candidate = path.resolve(_projectRoot, ...parts);
  if (!isWithin(candidate, _projectRoot)) {
    throw new Error(`[sandbox] 路径越过项目根目录: ${value}`);
  }
  return { value, candidate, canonical: canonicalizeCandidate(candidate) };
}

function configureSafety(config) {
  _projectRoot = fs.realpathSync.native(process.cwd());
  const safety = config.safety || {};
  const configuredRoots = safety.allowed_roots?.length ? safety.allowed_roots : ['.'];
  _allowedRoots = configuredRoots.map(value => {
    const resolved = projectRelative(value);
    if (!isWithin(resolved.canonical, _projectRoot)) {
      throw new Error(`[sandbox] allowed_root 越过项目根目录: ${value}`);
    }
    return resolved.canonical;
  });
  _neverBackup = (safety.never_backup || []).map(value => String(value).replaceAll('\\', '/'));
}

function resolveManagedPath(value) {
  const resolved = projectRelative(value);
  if (!_allowedRoots.some(root => isWithin(resolved.canonical, root))) {
    throw new Error(`[sandbox] 路径不在 safety.allowed_roots 内: ${value}`);
  }
  return resolved.candidate;
}

function assertManagedAbsolute(candidate, label) {
  const canonical = canonicalizeCandidate(candidate);
  if (!_allowedRoots.some(root => isWithin(canonical, root))) {
    throw new Error(`[sandbox] ${label} 解析后越过 safety.allowed_roots`);
  }
  return candidate;
}

function globMatch(value, pattern) {
  const escaped = pattern
    .replace(/[.+^${}()|[\]\\]/g, '\\$&')
    .replaceAll('**', '\u0000')
    .replaceAll('*', '[^/]*')
    .replaceAll('?', '[^/]')
    .replaceAll('\u0000', '.*');
  return new RegExp(`^${escaped}$`).test(value);
}

function isNeverBackup(candidate) {
  const relative = path.relative(_projectRoot, candidate).split(path.sep).join('/');
  return _neverBackup.some(pattern =>
    globMatch(relative, pattern) || globMatch(path.basename(relative), pattern)
  );
}

function fileHash(filePath) {
  if (!fs.existsSync(filePath)) return null;
  const content = fs.readFileSync(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

function dirSnapshot(dirPath) {
  if (!fs.existsSync(dirPath)) return null;
  assertManagedAbsolute(dirPath, dirPath);
  const result = {};
  for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {
    const fullPath = path.join(dirPath, entry.name);
    assertManagedAbsolute(fullPath, fullPath);
    if (entry.isSymbolicLink()) {
      throw new Error(`[sandbox] 拒绝快照符号链接: ${path.relative(_projectRoot, fullPath)}`);
    }
    if (isNeverBackup(fullPath)) continue;
    if (entry.isFile()) result[entry.name] = fileHash(fullPath);
    else if (entry.isDirectory()) result[`${entry.name}/`] = dirSnapshot(fullPath);
  }
  return result;
}

function envSnapshot(varNames) {
  return Object.fromEntries(varNames.map(name => [name, process.env[name] ?? null]));
}

function parseConfigFile(filePath) {
  if (!fs.existsSync(filePath)) return null;
  const ext = path.extname(filePath).toLowerCase();
  const content = fs.readFileSync(filePath, 'utf-8');
  if (ext === '.env') {
    const result = {};
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const index = trimmed.indexOf('=');
      if (index > 0) result[trimmed.slice(0, index).trim()] = trimmed.slice(index + 1).trim();
    }
    return result;
  }
  if (ext === '.json') return JSON.parse(content);
  return { _raw_hash: fileHash(filePath) };
}

function getSnapshotDir() {
  return path.resolve(_projectRoot || process.cwd(), 'e2e/sandbox/snapshots');
}

function getBackupDir() {
  return path.resolve(_projectRoot || process.cwd(), 'e2e/sandbox/backups');
}

function ensureInternalDir(dir) {
  if (!isWithin(dir, _projectRoot)) throw new Error('[sandbox] 内部存储越过项目根目录');
  fs.mkdirSync(dir, { recursive: true });
}

function snapshotFilePath() {
  return path.join(getSnapshotDir(), `snapshot_${process.pid}_${Date.now()}.json`);
}

function backupPathFor(candidate) {
  const relative = path.relative(_projectRoot, candidate);
  if (!relative || relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new Error(`[sandbox] 无法为越界路径创建备份: ${candidate}`);
  }
  const target = path.join(getBackupDir(), 'files', `${relative}.backup`);
  if (!isWithin(target, getBackupDir())) throw new Error('[sandbox] 备份路径越界');
  return target;
}

function backupFile(candidate) {
  if (!fs.existsSync(candidate) || isNeverBackup(candidate)) return;
  assertManagedAbsolute(candidate, candidate);
  const target = backupPathFor(candidate);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(candidate, target);
}

function backupDirectory(dirPath) {
  if (!fs.existsSync(dirPath)) return;
  for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {
    const fullPath = path.join(dirPath, entry.name);
    assertManagedAbsolute(fullPath, fullPath);
    if (entry.isSymbolicLink()) throw new Error(`[sandbox] 拒绝备份符号链接: ${fullPath}`);
    if (isNeverBackup(fullPath)) continue;
    if (entry.isFile()) backupFile(fullPath);
    else if (entry.isDirectory()) backupDirectory(fullPath);
  }
}

function restoreTree(rootPath, original, errors) {
  if (original === null) {
    if (fs.existsSync(rootPath)) fs.rmSync(assertManagedAbsolute(rootPath, rootPath), { recursive: true, force: true });
    return;
  }
  fs.mkdirSync(rootPath, { recursive: true });
  const currentNames = new Set(fs.readdirSync(rootPath));
  const originalNames = new Set(Object.keys(original).map(name => name.endsWith('/') ? name.slice(0, -1) : name));
  for (const name of currentNames) {
    const candidate = path.join(rootPath, name);
    assertManagedAbsolute(candidate, candidate);
    if (isNeverBackup(candidate)) continue;
    if (!originalNames.has(name)) fs.rmSync(candidate, { recursive: true, force: true });
  }
  for (const [name, value] of Object.entries(original)) {
    const cleanName = name.endsWith('/') ? name.slice(0, -1) : name;
    const candidate = path.join(rootPath, cleanName);
    assertManagedAbsolute(candidate, candidate);
    if (name.endsWith('/')) {
      restoreTree(candidate, value, errors);
    } else if (fileHash(candidate) !== value) {
      const backup = backupPathFor(candidate);
      if (!fs.existsSync(backup)) errors.push(`无法恢复 ${path.relative(_projectRoot, candidate)}：备份不存在`);
      else {
        fs.mkdirSync(path.dirname(candidate), { recursive: true });
        fs.copyFileSync(backup, candidate);
      }
    }
  }
}

export async function snapshot() {
  _config = loadConfig();
  configureSafety(_config);
  ensureInternalDir(getSnapshotDir());
  ensureInternalDir(getBackupDir());
  _snapshotPath = snapshotFilePath();
  const snap = { timestamp: new Date().toISOString(), directories: {}, files: {}, env_vars: {} };
  for (const dir of _config.snapshot?.directories || []) {
    const absolute = resolveManagedPath(dir);
    snap.directories[dir] = dirSnapshot(absolute);
    backupDirectory(absolute);
  }
  for (const file of _config.snapshot?.files || []) {
    const absolute = resolveManagedPath(file);
    if (isNeverBackup(absolute)) continue;
    snap.files[file] = { hash: fileHash(absolute), parsed: parseConfigFile(absolute) };
    backupFile(absolute);
  }
  snap.env_vars = envSnapshot(_config.snapshot?.env_vars || []);
  _snapshotData = snap;
  fs.writeFileSync(_snapshotPath, JSON.stringify(snap, null, 2), 'utf-8');
}

export async function restore() {
  if (!_snapshotData || !_config) return;
  const errors = [];
  for (const dir of _config.snapshot?.directories || []) {
    restoreTree(resolveManagedPath(dir), _snapshotData.directories[dir], errors);
  }
  for (const file of _config.snapshot?.files || []) {
    const original = _snapshotData.files[file];
    if (!original) continue;
    const absolute = resolveManagedPath(file);
    const currentHash = fileHash(absolute);
    if (original.hash === null) {
      if (currentHash !== null) fs.rmSync(assertManagedAbsolute(absolute, file), { force: true });
    } else if (currentHash !== original.hash) {
      const backup = backupPathFor(absolute);
      if (!fs.existsSync(backup)) errors.push(`无法恢复 ${file}：备份不存在`);
      else {
        fs.mkdirSync(path.dirname(absolute), { recursive: true });
        fs.copyFileSync(backup, absolute);
      }
    }
  }
  for (const [name, value] of Object.entries(_snapshotData.env_vars || {})) {
    if (value === null) delete process.env[name];
    else process.env[name] = value;
  }
  if (errors.length) throw new Error(`[sandbox] 恢复失败:\n${errors.join('\n')}`);
}

function collectTreeDiffs(base, current, original, diffs) {
  if (JSON.stringify(current) === JSON.stringify(original)) return;
  const keys = new Set([...Object.keys(current || {}), ...Object.keys(original || {})]);
  for (const key of keys) {
    const left = current?.[key];
    const right = original?.[key];
    if (typeof left === 'object' && typeof right === 'object') collectTreeDiffs(path.join(base, key), left, right, diffs);
    else if (left !== right) diffs.push(path.join(base, key));
  }
}

export async function verify() {
  if (!_snapshotData || !_config) return;
  const diffs = [];
  for (const dir of _config.snapshot?.directories || []) {
    collectTreeDiffs(dir, dirSnapshot(resolveManagedPath(dir)), _snapshotData.directories[dir], diffs);
  }
  for (const [file, original] of Object.entries(_snapshotData.files || {})) {
    if (fileHash(resolveManagedPath(file)) !== original.hash) diffs.push(file);
  }
  for (const name of _config.snapshot?.env_vars || []) {
    if ((process.env[name] ?? null) !== (_snapshotData.env_vars?.[name] ?? null)) diffs.push(`env:${name}`);
  }
  if (diffs.length) {
    console.error(`[sandbox] 环境验证失败: ${diffs.join(', ')}`);
    process.exitCode = 1;
  }
}

export function getSandboxEnv() {
  return {
    E2E_SANDBOX_MODE: 'true',
    E2E_UPLOAD_DIR: 'e2e/sandbox/uploads/',
    E2E_EXPORT_DIR: 'e2e/sandbox/exports/',
    E2E_LOG_DIR: 'e2e/sandbox/logs/'
  };
}

export function initSandboxDirs() {
  for (const dir of ['e2e/sandbox/uploads', 'e2e/sandbox/exports', 'e2e/sandbox/logs', 'e2e/sandbox/snapshots', 'e2e/sandbox/backups']) {
    fs.mkdirSync(path.resolve(process.cwd(), dir), { recursive: true });
  }
}

export function reset() {
  _snapshotData = null;
  _config = null;
  _snapshotPath = null;
  _projectRoot = null;
  _allowedRoots = [];
  _neverBackup = [];
}
