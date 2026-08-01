# 原因

MASE 2.4.0 的 `mase init` 生成项目后，立即执行同版本
`mase update --dry-run` 仍报告四项迁移，包括无意义的
`2.4.0 -> 2.4.0` 元数据更新。发布前的 wheel 消费者烟测发现该问题。

# 验收行为

对 generic、Python 和 Swift 三种新建项目，初始化后立即执行同版本
updater 时不产生 update/create/conflict；既有 generic 最小骨架行为保持不变。

# 影响范围

- Change Risk：L2；不改变 CLI 参数、公共 Schema、认证、数据或持久化行为。
- 内部实现与直接调用方：`mase_cli/config.py`、`init_project.py`、
  `update_project.py`，以及 `mase init` / `mase update` CLI 路径。
- 隐性分发依赖：`templates/stacks/common/gitignore.tpl` 会进入 wheel 运行时资源。
- 受保护行为：generic 项目仍保持可删除的空 `src/`、`tests/` 最小骨架；
  brownfield updater 的 sandbox、gitignore 和 toolchain 迁移继续生效。
- 禁止范围：不修改采用项目、现有项目文件、OpenSpec 主规范或发布版本号。

# 根因假设与 RED 证据

假设：init 未生成 updater 规范化后的全部字段和模板，因此同版本比较不相等。

RED：`test_fresh_init_requires_no_same_version_update` 修复前失败，返回四项差异：
`.mase.yaml`、`sandbox.config.json`、`tests/e2e/sandbox/`、`.gitignore`。

复扫：静态检索确认共享规则只被 init、update 与对应测试消费；方法签名、调用边和
外部副作用类型不变，仅让新项目首次产物与 updater 的目标状态一致。

# 测试方法

- 三栈幂等契约：`test_fresh_init_requires_no_same_version_update`。
- 初始化、更新、治理迁移聚焦回归：35 项。
- wheel 安装后执行 `mase init`、`mase check`、`mase update --dry-run`。
- 候选冻结后重新运行 Python、Node、仓库边界、OpenSpec 和分发完整性门禁。

# 回滚方式

回退本修复提交即可恢复旧初始化行为。变更只影响新建项目，不迁移或覆盖既有数据；
brownfield updater 行为保留，因此回退不需要数据恢复。

# Tasks

- [x] 1.1 建立 RED 证据
- [x] 1.2 实现最小修复并运行聚焦测试
