## ADDED Requirements

### Requirement: 框架与产品具有独立项目根
MASE 框架和采用 MASE 开发的磨耳朵产品 MUST 位于平级但不同的目录，且每个目录 MUST 有独立项目元数据、状态和 Git 仓库。

#### Scenario: 迁移完成
- **WHEN** 用户查看 `trae_projects` 目录
- **THEN** `MASE/` 与 `磨耳朵/` 同级存在
- **AND** 两个目录中的 `git rev-parse --show-toplevel` 返回不同路径

### Requirement: 产品文件只存在于产品根
磨耳朵的 Swift Package、产品源码、资源、产品测试、需求、OpenSpec、构建脚本和交付包 MUST 从 MASE 当前树移除并存在于磨耳朵根。

#### Scenario: 检查 MASE 当前树
- **WHEN** 执行 MASE 文件归属检查
- **THEN** MASE 不包含 Package.swift、Morerduo Swift 源、产品 Swift tests、产品 OpenSpec 或产品构建脚本

#### Scenario: 检查磨耳朵当前树
- **WHEN** 执行产品文件归属检查
- **THEN** 磨耳朵包含构建和完整验收所需的全部跟踪文件

### Requirement: 框架测试不依赖产品目录
MASE MUST 保留自己的 Python 与 Sandbox JavaScript 测试，并且这些测试 MUST 在磨耳朵目录不存在或不参与上下文时独立通过。

#### Scenario: 验证 MASE
- **WHEN** 在 MASE 根运行框架测试、OpenSpec strict 和 `mase check`
- **THEN** 所有门禁通过且命令不读取平级磨耳朵源码

### Requirement: 产品迁移后行为不变
磨耳朵 MUST 在新根目录通过迁移前相同的 Unit、Integration、Contract、Native E2E 和 app bundle 验收。

#### Scenario: 新目录完整验证
- **WHEN** 在磨耳朵根运行 `scripts/verify-morerduo.sh`
- **THEN** 49 Unit、53 Integration、60 Contract、20 E2E 与签名 app bundle 全部通过

### Requirement: 迁移可追溯且不造成双份大型缓存
迁移 MUST 记录来源提交并在删除源文件前建立可恢复目标；不得同时复制根 Swift `.build` 或 POC `.build` 大型缓存。

#### Scenario: 检查迁移 provenance
- **WHEN** 查看磨耳朵 README 和首个 Git 提交
- **THEN** 能识别来源 MASE 分支/提交和迁移日期

#### Scenario: 检查磁盘边界
- **WHEN** 迁移完成
- **THEN** MASE 根和产品 POC 中不存在旧 Swift `.build`，产品最多保留一份当前根构建缓存
