## Context

MASE 当前根目录同时是 Python 框架仓库和磨耳朵 Swift Package：产品占用 `src/`、Swift tests、Package 清单、资源、产品需求、产品 OpenSpec 与约 2GB 构建缓存。两个项目共享一个 Git、一个根目录和一套检查入口，违反 MASE v2 的内容边界。

目标平级目录不存在。用户硬盘空间有限，因此迁移不得先复制两个大型 `.build`；当前产品已完整验收，MASE Git 也保留其历史。

## Goals / Non-Goals

**Goals:**

- 建立 `/Users/dylanren/Documents/trae_projects/磨耳朵` 独立项目和本地 Git。
- 新路径保留全部产品源、需求、测试、OpenSpec、脚本和验收包，并通过完整验证。
- MASE 根目录不再包含或依赖任何磨耳朵产品文件。
- 迁移过程中始终至少保留一份可恢复源码和验收证据。

**Non-Goals:**

- 不改变磨耳朵功能、架构、测试语义或发布方式。
- 不重写原 MASE Git 历史，也不运行高成本 history filter。
- 不推送任何外部仓库。
- 不保留可重建的 POC `.build` 缓存。

## Decisions

### D1：复制源文件，移动大型生成缓存

先把全部跟踪产品文件复制到目标目录并校验；根 `.build` 直接移动以避免瞬时双份 1.1GB；POC `.build` 不迁移，在新仓库验证后删除。`dist/磨耳朵.app` 随产品移动。

### D2：新 Git 从验收快照开始

目标目录执行独立 `git init`，首次提交记录来源仓库、来源分支和提交 `a28c4f6`。完整早期历史仍可在 MASE 旧提交中查询；不使用 filter-repo，以降低风险和磁盘占用。

### D3：文件归属按产品行为划分

迁移 Package.swift/Package.resolved、`src`、resources、Swift unit/integration/contract/support/E2E、产品构建脚本、需求资料、产品 OpenSpec/master 和 dist。`tests/e2e/sandbox.test.js` 属于 MASE 框架，移动到 MASE 的 `tests/sandbox/` 并更新 Vitest 配置。

### D4：新项目采用 MASE v2 元数据

目标增加 `.mase.yaml`（Standard/Swift）、独立 README、Gitignore、核心规则和 generated IDE adapters。完成的 macOS change 状态迁移到 v2/complete，并保留原验证摘要。

### D5：验证后才删除源

复制后先比较跟踪文件清单与哈希，再从新目录运行 `verify-morerduo.sh`。只有验证通过并完成新仓库首个提交后，才在 MASE 执行产品路径删除和缓存清理。

## Risks / Trade-offs

- [移动 `.build` 后缓存含旧绝对路径] → SwiftPM 可重新规划；若失效，删除新目录缓存重建，源码不受影响。
- [漏迁混合 tests/e2e 文件] → 显式排除唯一框架文件 `sandbox.test.js`，分别验证 Swift E2E 和 Vitest。
- [新仓库缺少早期逐提交历史] → README/provenance 记录来源提交，MASE 历史继续可查。
- [外部目录写入失败] → 在删除 MASE 文件前停止，原仓库保持完整。
- [空间不足] → 不复制两处 `.build`，删除 846MB POC 缓存后再必要重建。

## Migration Plan

1. 生成迁移 manifest，复制所有小型/跟踪产品文件到目标。
2. 复制 MASE v2 项目元数据和 provenance，移动 dist 与根 `.build`。
3. 比较迁移清单、关键哈希与文件数量。
4. 在目标运行完整产品验证并创建独立本地提交。
5. 在 MASE 移动 Sandbox JS 测试，删除全部产品跟踪路径与 POC cache。
6. 运行 MASE Python/Vitest/OpenSpec/check，确认两个根互不依赖并提交。

回滚：在 MASE 删除前直接移除目标即可；在 MASE 删除后可从目标仓库、目标工作树或 MASE 父提交恢复。

## Open Questions

无。目标路径、Git 模式和缓存策略已按用户的物理隔离与磁盘约束确定。
