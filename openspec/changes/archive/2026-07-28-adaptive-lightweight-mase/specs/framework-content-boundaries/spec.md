## ADDED Requirements

### Requirement: 框架 manifest 定义发布边界
MASE MUST 通过 manifest 明确版本、规范源、生成目标、运行时资源和默认排除目录。

#### Scenario: 安装框架
- **WHEN** 用户执行框架安装
- **THEN** 只分发 manifest 列出的 rules、profiles、schemas、templates、agents、skills 和现行文档

### Requirement: 历史培训和产品实例不进入默认上下文
MASE MUST 将 archive、training、generated site 和 examples 标记为非规范内容，CLI 与 Agent 默认不得扫描这些目录。

#### Scenario: Agent 获取框架规范
- **WHEN** Agent 请求现行 MASE 规则
- **THEN** 检索结果不包含历史设计稿、培训幻灯片或磨耳朵产品文件

### Requirement: 版本与许可证一致
MASE MUST 从单一包元数据取得版本，并确保 README、安装器、manifest、Python 包和 Node 辅助包使用一致版本与许可证声明。

#### Scenario: 发布新版本
- **WHEN** 构建 MASE 发布包
- **THEN** 自动检查所有发布表面不存在冲突版本或许可证

### Requirement: 生成物不得成为人工规范源
MASE MUST 标记 IDE 适配文件、状态报告、追踪矩阵、培训 HTML/PPT 和归档快照为 generated 或 non-normative。

#### Scenario: 生成物被人工修改
- **WHEN** 更新器发现 generated 文件被人工修改
- **THEN** 系统保留备份并提示修改规范源后重新生成
