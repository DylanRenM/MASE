## 1. Schema 与兼容领域模型

- [x] 1.1 扩展 `.mase.yaml` 与 change state Schema，加入主 stack、toolchains、产品属性、change 影响面和结构化证据模型
- [x] 1.2 引入统一 Schema 校验入口，并让项目检查、状态、迁移和报告共享同一解析结果
- [x] 1.3 实现旧 v1.3/v2 状态兼容读取及明确的 legacy/stale 标记
- [x] 1.4 增加损坏 YAML、非法枚举、复合 stack、缺失字段和未知 Schema 版本测试

## 2. 风险 GatePlan 与可执行证据

- [x] 2.1 建立标准风险触发器注册表及 Profile/Capability 局部升级算法
- [x] 2.2 实现由 Profile、风险、产品属性和 change 影响面推导 GatePlan，并阻止删除硬门禁
- [x] 2.3 实现自动 Gate Runner，原子记录命令、退出码、时间、平台、Git 与日志证据
- [x] 2.4 实现命令、环境和日志中的凭据脱敏测试
- [x] 2.5 实现人工证据记录及自动/人工 gate 类型匹配校验
- [x] 2.6 实现基于输入路径、工作区指纹、日志和制品哈希的证据新鲜度判定
- [x] 2.7 增加 passed、failed、stale、missing、制品被替换和无效人工证据回归测试

## 3. Brownfield 遗留基线

- [x] 3.1 定义 `.mase/baseline.yaml` Schema、失败签名、负责人、到期和处置 change 模型
- [x] 3.2 实现基线候选采集、审核写入、dry-run 和备份流程
- [x] 3.3 实现当前失败与基线的集合/签名比较及 `passed_with_baseline` 状态
- [x] 3.4 实现硬门禁不可普通基线化及独立期限风险接受校验
- [x] 3.5 实现新增、恶化、已解决、过期和重复运行的 Brownfield 回归测试

## 4. Portfolio 状态与诊断

- [x] 4.1 将无参数 `mase status` 改为零/多 change portfolio 表格与 JSON 输出
- [x] 4.2 增加 change 依赖、互斥和文件影响范围模型及循环/冲突检测
- [x] 4.3 修正 verify/retro/release/complete/archived 语义并派生 ready_for_gate、ready_to_complete 等状态
- [x] 4.4 定义稳定 CLI 退出码和诊断对象，捕获配置、Schema、路径和选择错误且默认不输出 traceback
- [x] 4.5 增加多 change、零 change、缺失依赖、循环依赖、路径攻击和部分状态损坏测试

## 5. 非破坏迁移与发布验证

- [x] 5.1 扩展 `mase update --dry-run`，预览 metadata、stack/toolchains、状态、证据、基线和适配文件变化
- [x] 5.2 实现迁移备份、冲突保留、幂等及无法验证的旧 passed 证据降级为 stale
- [x] 5.3 用 MASE 自身、磨耳朵和一个合成 Brownfield fixture 执行迁移及回滚演练
- [x] 5.4 更新框架版本、manifest、模板、Profile、项目规则、用户指南和离线安装依赖
- [x] 5.5 运行 CLI 全量单元/集成测试、包安装 smoke、`mase check/status/update` 端到端回归并记录证据
