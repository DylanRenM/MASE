## 1. 契约测试与数据基线

- [x] 1.1 为 Profile 选择、capability 风险升级和分级门禁编写契约测试
- [x] 1.2 为唯一状态、状态不一致检测、规则生成哈希和派生报告编写测试
- [x] 1.3 为 generic/python/swift 初始化与 stack-aware 合规检查编写 CLI 集成测试
- [x] 1.4 为 doctor/status/metrics 和非破坏 update 编写行为测试

## 2. Manifest、Profile 与状态核心

- [x] 2.1 新增统一 framework manifest、Lite/Standard/Strict Profile 和状态 schema
- [x] 2.2 实现 Profile 加载、风险升级、适用产物与门禁计算模块
- [x] 2.3 实现 change 状态读取、任务进度比对、证据汇总和归档快照接口
- [x] 2.4 实现核心规则到 IDE 适配文件的确定性生成与 source hash 冲突检测

## 3. 跨技术栈 CLI

- [x] 3.1 将 init 模板从 Python 代码中移出，支持 generic/python/swift 与 Profile 参数
- [x] 3.2 将 check 改为 manifest、Profile 和 stack 驱动，并提供 JSON 输出
- [x] 3.3 新增 doctor、status、metrics 命令及真实 Token/代理指标区分
- [x] 3.4 将 update 改为 manifest 计划、dry-run、generated 文件识别、备份和冲突报告
- [x] 3.5 统一 Python/Node/manifest/README/安装器版本与 MIT 许可证

## 4. 规则、模板、Agent 与 Skill 轻量化

- [x] 4.1 将 project-rules 改为短核心规则与 Profile 路由，并生成四个 IDE 适配文件
- [x] 4.2 统一 change state/spec/task 模板，弃用重复 `.openspec.yaml` 和日常 master 双写模板
- [x] 4.3 更新四个 Agent 为 Profile 路由、批量澄清、分级 TDD 和风险质量门禁
- [x] 4.4 将高 Token Skills 改成短路由器加按需 references，并加入任务最小 reads 约束

## 5. 文档与仓库边界

- [x] 5.1 重写现行框架、结构、编码和用户指南，使其只描述 MASE v2 单一流程源
- [x] 5.2 在 manifest 中排除 archive/training/generated/examples，并为历史设计添加非规范或 superseded 标记
- [x] 5.3 将框架安装器限制为 manifest 声明资源，产品脚本与培训生成物不再默认分发

## 6. 验证与迁移

- [x] 6.1 运行框架单元/集成测试、OpenSpec strict 校验和 CLI 多 stack 冒烟
- [x] 6.2 对模拟 v1.3 项目执行 update dry-run、备份、冲突与幂等迁移测试
- [x] 6.3 运行磨耳朵完整验证，确认框架改造不改变 macOS MVP
- [x] 6.4 更新 change 状态与验证摘要，确认任务、阶段和证据一致
