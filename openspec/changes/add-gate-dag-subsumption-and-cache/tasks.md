## 1. DAG 与证据契约

- [x] 1.1 为通用 requires、环路、拓扑计划和 subsumed 状态补充 Schema/RED 测试
- [x] 1.2 为依赖锁、工具链、fixture/config、候选和环境摘要补充缓存失效测试

## 2. 运行时

- [x] 2.1 实现 Gate DAG 校验、传递前序选择和统一阻塞逻辑
- [x] 2.2 扩展 execution signature/cache key，并实现可审计 subsumed evidence
- [x] 2.3 收紧 covers 等价/超集校验与同对象冗余统计

## 3. 集成

- [x] 3.1 更新 Schema、MASE gate 配置、规则和文档
- [x] 3.2 运行定向测试并记录实际影响复扫
