/**
 * E2E Sandbox 单元测试
 *
 * 运行: npx vitest run tests/e2e/sandbox.test.js
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import * as sandbox from '../../skills/webapp-testing/sandbox.js';

// 原始工作目录，用于测试后恢复
const originalCwd = process.cwd();
let testDir;

beforeEach(() => {
  // 创建独立的临时测试环境
  testDir = path.join(os.tmpdir(), `sandbox_test_${Date.now()}_${Math.random().toString(36).slice(2)}`);
  fs.mkdirSync(testDir, { recursive: true });
  process.chdir(testDir);
  sandbox.reset();
});

afterEach(() => {
  // 恢复工作目录并清理
  process.chdir(originalCwd);
  if (testDir && fs.existsSync(testDir)) {
    fs.rmSync(testDir, { recursive: true, force: true });
  }
});

describe('snapshot()', () => {
  it('应该在没有 sandbox.config.json 时使用默认配置并正常完成', async () => {
    await sandbox.snapshot();

    const snapDir = path.join(testDir, 'e2e/sandbox/snapshots');
    expect(fs.existsSync(snapDir)).toBe(true);
    const files = fs.readdirSync(snapDir);
    expect(files.length).toBeGreaterThan(0);
  });

  it('应该捕获 .env 文件快照', async () => {
    fs.writeFileSync(path.join(testDir, '.env'), 'APP_ENV=test\nDEBUG=true\n');

    await sandbox.snapshot();

    const snapDir = path.join(testDir, 'e2e/sandbox/snapshots');
    const snapFiles = fs.readdirSync(snapDir);
    const snapContent = JSON.parse(
      fs.readFileSync(path.join(snapDir, snapFiles[0]), 'utf-8')
    );

    expect(snapContent.files['.env']).toBeDefined();
    expect(snapContent.files['.env'].hash).toBeDefined();
  });

  it('应该捕获目录快照', async () => {
    fs.mkdirSync(path.join(testDir, 'data/uploads'), { recursive: true });
    fs.writeFileSync(path.join(testDir, 'data/uploads', 'before.txt'), 'original');

    fs.writeFileSync(path.join(testDir, 'sandbox.config.json'), JSON.stringify({
      snapshot: {
        directories: ['data/uploads/'],
        files: [],
        env_vars: []
      }
    }));

    await sandbox.snapshot();

    const snapDir = path.join(testDir, 'e2e/sandbox/snapshots');
    const snapFiles = fs.readdirSync(snapDir);
    const snapContent = JSON.parse(
      fs.readFileSync(path.join(snapDir, snapFiles[0]), 'utf-8')
    );

    expect(snapContent.directories['data/uploads/']).toBeDefined();
    expect(snapContent.directories['data/uploads/']['before.txt']).toBeDefined();
  });
});

describe('restore()', () => {
  it('应该恢复被修改的 .env 文件', async () => {
    const originalContent = 'APP_ENV=production\nDEBUG=false\n';
    fs.writeFileSync(path.join(testDir, '.env'), originalContent);

    await sandbox.snapshot();

    // 模拟测试修改 .env
    fs.writeFileSync(path.join(testDir, '.env'), 'APP_ENV=test\nDEBUG=true\nCHANGED=yes\n');

    await sandbox.restore();

    const restored = fs.readFileSync(path.join(testDir, '.env'), 'utf-8');
    expect(restored).toBe(originalContent);
  });

  it('应该删除测试期间新增的文件', async () => {
    fs.mkdirSync(path.join(testDir, 'data/uploads'), { recursive: true });
    fs.writeFileSync(path.join(testDir, 'data/uploads', 'original.txt'), 'keep me');

    fs.writeFileSync(path.join(testDir, 'sandbox.config.json'), JSON.stringify({
      snapshot: {
        directories: ['data/uploads/'],
        files: [],
        env_vars: []
      }
    }));

    await sandbox.snapshot();

    // 模拟测试新增文件
    fs.writeFileSync(path.join(testDir, 'data/uploads', 'test_artifact.txt'), 'test data');

    await sandbox.restore();

    expect(
      fs.existsSync(path.join(testDir, 'data/uploads', 'test_artifact.txt'))
    ).toBe(false);

    expect(
      fs.existsSync(path.join(testDir, 'data/uploads', 'original.txt'))
    ).toBe(true);
  });
});

describe('verify()', () => {
  it('应该在环境一致时通过验证', async () => {
    fs.writeFileSync(path.join(testDir, '.env'), 'APP_ENV=test\n');

    await sandbox.snapshot();
    await sandbox.verify();

    // 重置 exitCode 避免影响其他测试
    const exitCode = process.exitCode;
    process.exitCode = 0;
    expect(exitCode).not.toBe(1);
  });

  it('应该在文件被修改时检测到不一致', async () => {
    fs.writeFileSync(path.join(testDir, '.env'), 'APP_ENV=test\n');

    await sandbox.snapshot();

    // 修改文件
    fs.writeFileSync(path.join(testDir, '.env'), 'APP_ENV=changed\n');

    await sandbox.verify();

    expect(process.exitCode).toBe(1);
    process.exitCode = 0;
  });

  it('应该在目录有新增文件时检测到不一致', async () => {
    fs.mkdirSync(path.join(testDir, 'data/uploads'), { recursive: true });

    fs.writeFileSync(path.join(testDir, 'sandbox.config.json'), JSON.stringify({
      snapshot: {
        directories: ['data/uploads/'],
        files: [],
        env_vars: []
      }
    }));

    await sandbox.snapshot();

    // 新增文件
    fs.writeFileSync(path.join(testDir, 'data/uploads', 'leftover.txt'), 'oops');

    await sandbox.verify();

    expect(process.exitCode).toBe(1);
    process.exitCode = 0;
  });
});

describe('restore() + verify() 端到端', () => {
  it('snapshot → 修改 → restore → verify 应全部通过', async () => {
    // 准备初始环境
    fs.mkdirSync(path.join(testDir, 'data/uploads'), { recursive: true });
    fs.writeFileSync(path.join(testDir, 'data/uploads', 'a.txt'), 'hello');
    fs.writeFileSync(path.join(testDir, 'data/uploads', 'b.txt'), 'world');
    fs.writeFileSync(path.join(testDir, '.env'), 'KEY=value\n');

    fs.writeFileSync(path.join(testDir, 'sandbox.config.json'), JSON.stringify({
      snapshot: {
        directories: ['data/uploads/'],
        files: ['.env'],
        env_vars: []
      }
    }));

    await sandbox.snapshot();

    // 模拟测试修改
    fs.writeFileSync(path.join(testDir, 'data/uploads', 'c.txt'), 'new file');
    fs.writeFileSync(path.join(testDir, 'data/uploads', 'a.txt'), 'modified');
    fs.writeFileSync(path.join(testDir, '.env'), 'KEY=changed\n');

    await sandbox.restore();
    await sandbox.verify();

    const exitCode = process.exitCode;
    process.exitCode = 0;
    expect(exitCode).not.toBe(1);

    // 确认恢复结果
    expect(fs.readFileSync(path.join(testDir, '.env'), 'utf-8')).toBe('KEY=value\n');
    expect(fs.readFileSync(path.join(testDir, 'data/uploads', 'a.txt'), 'utf-8')).toBe('hello');
    expect(fs.readFileSync(path.join(testDir, 'data/uploads', 'b.txt'), 'utf-8')).toBe('world');
    expect(fs.existsSync(path.join(testDir, 'data/uploads', 'c.txt'))).toBe(false);
  });
});
