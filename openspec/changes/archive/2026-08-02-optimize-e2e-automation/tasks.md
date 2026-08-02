## 1. Manifest 与选测契约

- [x] 1.1 为 `mase-test-manifest/v1` 编写失败测试，覆盖合法清单、路径逃逸、非法 tier、重复 ID 和 P0 必填语义
- [x] 1.2 实现测试 manifest Schema、解析模型和安全校验
- [x] 1.3 编写影响路径、Capability scope、稳定排序和 P0 保守回退的选择测试
- [x] 1.4 实现通用测试选择器及机器可读选择摘要

## 2. GatePlan 与证据集成

- [x] 2.1 编写 `test_tiers`、`{selected_tests}`、plan 输出和旧 gate 兼容失败测试
- [x] 2.2 扩展 gate Schema、模型、命令展开、执行签名和 plan 诊断
- [x] 2.3 编写标准诊断、unknown 回退和 retry/flaky 证据失败测试
- [x] 2.4 扩展诊断 Schema、Gate Runner 环境与 Evidence 模型并绑定诊断制品

## 3. 过程与分发资源

- [x] 3.1 更新核心规则、Profile/risk 调度和 `docs/MASE-framework.md` 的 E2E 分层与门禁语义
- [x] 3.2 更新 Web E2E Skill、质量 Agent 和参考规范，提供 Playwright MASE reporter adapter
- [x] 3.3 增加测试 manifest/gate/framework contract 模板与 Schema，并更新 framework manifest、wheel 和分发完整性契约
- [x] 3.4 更新培训源中的 E2E 选测、隔离、诊断和人工职责内容并重新生成受保护课件

## 4. Clean-room 采用契约验证

- [x] 4.1 生成临时采用项目的 Capability-to-Test manifest，并校验 UI contract/P0/P1 Schema 与路径安全
- [x] 4.2 在临时采用项目中验证动态选择、旧静态 gate 兼容、隔离 fixture 协议和诊断 reporter
- [x] 4.3 增加框架仓库边界契约，并验证精确 UI 命中、未命中全 P0 回退及非 UI change 不误触发

## 5. 最终验证

- [x] 5.1 运行 OpenSpec 严格校验、MASE manifest/gate/证据/Profile 聚焦测试
- [x] 5.2 运行 MASE 框架全量回归、分发完整性和仓库边界审计
- [x] 5.3 运行 clean-room 临时采用项目的 manifest、GatePlan、Gate Runner、reporter 和兼容性验证
- [x] 5.4 记录兼容性、性能、flaky 指标和回滚验证摘要
