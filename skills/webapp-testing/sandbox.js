/**
 * E2E Sandbox — 环境隔离与自动恢复
 *
 * 三层防线：
 *   1. 状态快照与恢复 — beforeAll 捕获快照，afterAll 恢复
 *   2. 写入重定向      — 通过环境变量将写操作定向到临时目录
 *   3. 环境健康检查    — 恢复后验证一致性
 *
 * 用法（在 spec 文件中）：
 *   import { snapshot, restore, verify } from '../helpers/sandbox.js';
 *   test.beforeAll(async () => { await snapshot(); });
 *   test.afterAll(async () => { await restore(); await verify(); });
 */

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execSync } from 'node:child_process';

// ---- 配置加载 ----

function loadConfig() {
  const configPath = path.resolve(process.cwd(), 'sandbox.config.json');
  if (!fs.existsSync(configPath)) {
    console.warn('[sandbox] sandbox.config.json 未找到，使用默认空配置（仅监控 .env）');
    return {
      snapshot: { directories: [], files: ['.env'], env_vars: [] },
      validation: { strict: true }
    };
  }
  return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
}

// ---- 文件哈希 ----

function fileHash(filePath) {
  if (!fs.existsSync(filePath)) return null;
  const content = fs.readFileSync(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

// ---- 目录快照 ----

function dirSnapshot(dirPath) {
  if (!fs.existsSync(dirPath)) return null;
  const result = {};
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    if (entry.isFile()) {
      result[entry.name] = fileHash(fullPath);
    } else if (entry.isDirectory()) {
      result[entry.name + '/'] = dirSnapshot(fullPath);
    }
  }
  return result;
}

// ---- 环境变量快照 ----

function envSnapshot(varNames) {
  const result = {};
  for (const name of varNames) {
    result[name] = process.env[name] || null;
  }
  return result;
}

// ---- 配置文件解析 ----

function parseConfigFile(filePath) {
  if (!fs.existsSync(filePath)) return null;
  const ext = path.extname(filePath).toLowerCase();
  const content = fs.readFileSync(filePath, 'utf-8');

  if (ext === '.env') {
    // .env 文件解析
    const result = {};
    const lines = content.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIdx = trimmed.indexOf('=');
      if (eqIdx > 0) {
        result[trimmed.slice(0, eqIdx).trim()] = trimmed.slice(eqIdx + 1).trim();
      }
    }
    return result;
  }

  if (ext === '.json') {
    return JSON.parse(content);
  }

  if (ext === '.yaml' || ext === '.yml') {
    // 简单 YAML 解析（仅支持顶层键值对）
    const result = {};
    const lines = content.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const colonIdx = trimmed.indexOf(':');
      if (colonIdx > 0 && !trimmed.startsWith(' ') && !trimmed.startsWith('\t')) {
        result[trimmed.slice(0, colonIdx).trim()] = trimmed.slice(colonIdx + 1).trim();
      }
    }
    return result;
  }

  // 未知格式：记录原始内容哈希
  return { _raw_hash: fileHash(filePath) };
}

// ---- 快照存储路径 ----

function getSnapshotDir() {
  return path.resolve(process.cwd(), 'e2e/sandbox/snapshots');
}

function ensureSnapshotDir() {
  const dir = getSnapshotDir();
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function snapshotFilePath() {
  // 每个 spec 文件一个快照文件，用时间戳 + PID 区分
  const pid = process.pid;
  const ts = Date.now();
  return path.join(getSnapshotDir(), `snapshot_${pid}_${ts}.json`);
}

// ---- 备份目录 ----

function getBackupDir() {
  return path.resolve(process.cwd(), 'e2e/sandbox/backups');
}

function ensureBackupDir() {
  const dir = getBackupDir();
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

/**
 * 递归备份目录内所有文件
 */
function backupDirectory(dirPath, basePath = '') {
  if (!fs.existsSync(dirPath)) return;
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    const relPath = basePath ? path.join(basePath, entry.name) : entry.name;
    if (entry.isFile()) {
      const backupPath = path.join(getBackupDir(), relPath + '.backup');
      const backupParent = path.dirname(backupPath);
      if (!fs.existsSync(backupParent)) {
        fs.mkdirSync(backupParent, { recursive: true });
      }
      fs.copyFileSync(fullPath, backupPath);
    } else if (entry.isDirectory()) {
      backupDirectory(fullPath, relPath);
    }
  }
}

// ================================================================
//  公开 API
// ================================================================

let _snapshotData = null;
let _config = null;
let _snapshotPath = null;

/**
 * 捕获环境快照
 * 在 beforeAll 中调用
 */
export async function snapshot() {
  _config = loadConfig();
  ensureSnapshotDir();
  ensureBackupDir();
  _snapshotPath = snapshotFilePath();

  console.log('[sandbox] 捕获环境快照...');

  const snap = {
    timestamp: new Date().toISOString(),
    directories: {},
    files: {},
    env_vars: {}
  };

  // 目录快照（含备份）
  for (const dir of _config.snapshot.directories || []) {
    const absPath = path.resolve(process.cwd(), dir);
    snap.directories[dir] = dirSnapshot(absPath);
    // 备份目录内所有文件
    backupDirectory(absPath);
  }

  // 文件快照（含备份）
  for (const file of _config.snapshot.files || []) {
    const absPath = path.resolve(process.cwd(), file);
    snap.files[file] = {
      hash: fileHash(absPath),
      parsed: parseConfigFile(absPath)
    };
    // 备份文件内容
    if (fs.existsSync(absPath)) {
      const backupPath = path.join(getBackupDir(), path.basename(file) + '.backup');
      fs.copyFileSync(absPath, backupPath);
    }
  }

  // 环境变量快照
  snap.env_vars = envSnapshot(_config.snapshot.env_vars || []);

  _snapshotData = snap;
  fs.writeFileSync(_snapshotPath, JSON.stringify(snap, null, 2), 'utf-8');
  console.log(`[sandbox] 快照已保存: ${_snapshotPath}`);
}

/**
 * 恢复环境到快照状态
 * 在 afterAll 中调用
 */
export async function restore() {
  if (!_snapshotData || !_config) {
    console.warn('[sandbox] 无快照数据，跳过恢复');
    return;
  }

  console.log('[sandbox] 恢复环境...');
  const snap = _snapshotData;
  const errors = [];

  // 恢复目录：删除快照中不存在的新增文件
  for (const dir of _config.snapshot.directories || []) {
    const absPath = path.resolve(process.cwd(), dir);
    if (!fs.existsSync(absPath)) continue;

    const currentSnap = dirSnapshot(absPath);
    const originalSnap = snap.directories[dir];

    if (!originalSnap) continue;

    // 删除新增文件
    for (const [name, hash] of Object.entries(currentSnap || {})) {
      if (!(name in originalSnap)) {
        const targetPath = path.join(absPath, name);
        if (name.endsWith('/')) {
          fs.rmSync(targetPath, { recursive: true, force: true });
          console.log(`  [sandbox] 删除新增目录: ${path.join(dir, name)}`);
        } else {
          fs.unlinkSync(targetPath);
          console.log(`  [sandbox] 删除新增文件: ${path.join(dir, name)}`);
        }
      }
    }

    // 恢复被修改的文件
    for (const [name, originalHash] of Object.entries(originalSnap)) {
      const filePath = path.join(absPath, name);
      const currentHash = currentSnap?.[name];
      if (currentHash && currentHash !== originalHash) {
        // 文件被修改，从备份恢复
        const backupPath = path.join(getBackupDir(), name + '.backup');
        if (fs.existsSync(backupPath)) {
          fs.copyFileSync(backupPath, filePath);
          console.log(`  [sandbox] 恢复文件: ${path.join(dir, name)}`);
        } else {
          errors.push(`无法恢复 ${path.join(dir, name)}：备份不存在`);
        }
      }
    }
  }

  // 恢复文件
  for (const file of _config.snapshot.files || []) {
    const backupPath = path.join(getBackupDir(), path.basename(file) + '.backup');
    const absPath = path.resolve(process.cwd(), file);
    const currentHash = fileHash(absPath);
    const originalHash = snap.files[file]?.hash;

    if (originalHash && currentHash !== originalHash) {
      if (fs.existsSync(backupPath)) {
        fs.copyFileSync(backupPath, absPath);
        console.log(`  [sandbox] 恢复文件: ${file}`);
      } else {
        // 文件原本不存在，现在被创建了 → 删除
        if (!originalHash && currentHash) {
          fs.unlinkSync(absPath);
          console.log(`  [sandbox] 删除新增文件: ${file}`);
        } else {
          errors.push(`无法恢复 ${file}：备份不存在`);
        }
      }
    }
  }

  // 恢复环境变量
  for (const [name, originalValue] of Object.entries(snap.env_vars || {})) {
    if (originalValue === null) {
      delete process.env[name];
    } else {
      process.env[name] = originalValue;
    }
  }

  if (errors.length > 0) {
    console.error('[sandbox] 恢复过程中出现错误:');
    errors.forEach(e => console.error(`  - ${e}`));
  }

  console.log('[sandbox] 环境恢复完成');
}

/**
 * 验证环境是否与快照一致
 * 在 afterAll 中 restore() 之后调用
 */
export async function verify() {
  if (!_snapshotData || !_config) {
    console.warn('[sandbox] 无快照数据，跳过验证');
    return;
  }

  console.log('[sandbox] 验证环境一致性...');
  const snap = _snapshotData;
  const diffs = [];

  // 验证目录
  for (const dir of _config.snapshot.directories || []) {
    const absPath = path.resolve(process.cwd(), dir);
    const currentSnap = dirSnapshot(absPath);
    const originalSnap = snap.directories[dir];

    const allKeys = new Set([
      ...Object.keys(currentSnap || {}),
      ...Object.keys(originalSnap || {})
    ]);

    for (const key of allKeys) {
      if (currentSnap?.[key] !== originalSnap?.[key]) {
        diffs.push({
          type: 'file',
          path: path.join(dir, key),
          expected: originalSnap?.[key] || '(不存在)',
          actual: currentSnap?.[key] || '(不存在)'
        });
      }
    }
  }

  // 验证文件
  for (const file of _config.snapshot.files || []) {
    const absPath = path.resolve(process.cwd(), file);
    const currentHash = fileHash(absPath);
    const originalHash = snap.files[file]?.hash;

    if (currentHash !== originalHash) {
      diffs.push({
        type: 'file',
        path: file,
        expected: originalHash || '(不存在)',
        actual: currentHash || '(不存在)'
      });
    }
  }

  // 验证环境变量
  for (const name of _config.snapshot.env_vars || []) {
    const currentValue = process.env[name] || null;
    const originalValue = snap.env_vars?.[name] || null;
    if (currentValue !== originalValue) {
      diffs.push({
        type: 'env',
        path: name,
        expected: originalValue || '(未设置)',
        actual: currentValue || '(未设置)'
      });
    }
  }

  if (diffs.length > 0) {
    console.error('[sandbox] 环境验证失败！以下状态与快照不一致:\n');
    for (const diff of diffs) {
      console.error(`  [${diff.type}] ${diff.path}`);
      console.error(`    期望: ${diff.expected}`);
      console.error(`    实际: ${diff.actual}\n`);
      console.error('清理命令:');
      console.error(`    rm -rf e2e/sandbox/uploads/* e2e/sandbox/exports/*`);
      console.error(`    并检查生产目录是否有残留文件\n`);
    }
    console.error('[sandbox] 测试已阻止，请手动清理后再运行。');
    process.exitCode = 1;
  } else {
    console.log('[sandbox] 环境验证通过 — 无污染');
  }
}

/**
 * 获取 sandbox 环境变量（用于 playwright.config.js 注入）
 */
export function getSandboxEnv() {
  return {
    E2E_SANDBOX_MODE: 'true',
    E2E_UPLOAD_DIR: 'e2e/sandbox/uploads/',
    E2E_EXPORT_DIR: 'e2e/sandbox/exports/',
    E2E_LOG_DIR: 'e2e/sandbox/logs/'
  };
}

/**
 * 初始化 sandbox 目录结构
 */
export function initSandboxDirs() {
  const dirs = [
    'e2e/sandbox/uploads',
    'e2e/sandbox/exports',
    'e2e/sandbox/logs',
    'e2e/sandbox/snapshots',
    'e2e/sandbox/backups'
  ];
  for (const dir of dirs) {
    const absPath = path.resolve(process.cwd(), dir);
    if (!fs.existsSync(absPath)) {
      fs.mkdirSync(absPath, { recursive: true });
    }
  }
}

/**
 * 重置模块状态（供测试使用）
 */
export function reset() {
  _snapshotData = null;
  _config = null;
  _snapshotPath = null;
}
