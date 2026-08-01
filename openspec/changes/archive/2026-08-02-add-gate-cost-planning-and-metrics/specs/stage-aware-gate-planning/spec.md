## ADDED Requirements

### Requirement: GatePlan 成本按目标时点分组
GatePlan SHALL 将 development、merge、release、observe 的预计成本分别展示，并 SHALL 对尚未请求的发布阶段标记为延迟执行而非当前阻塞。

#### Scenario: 只请求开发验证
- **WHEN** 调用者目标为 development
- **THEN** 计划显示开发预计耗时，并将合并和发布成本作为后续信息而非当前必做项
