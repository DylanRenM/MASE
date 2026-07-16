---
change: "<change-name>"
created: "YYYY-MM-DD"
agent: "agent-3-development"
---

## 系统架构图
```
<ASCII 架构图或描述>
```

## 技术栈决策表
| 决策点 | 候选方案 | 最终选择 | 理由 |
|--------|---------|---------|------|
| <决策> | <候选1>, <候选2> | <选择> | <理由> |

## 组件/模块边界
### <模块名>
- 职责: <单一职责>
- 输入: <接口输入>
- 输出: <接口输出>
- 依赖: <依赖的其他模块>

## 接口协议
### <接口名>
- 协议: <HTTP/gRPC/函数调用>
- 格式: <JSON/Protobuf>
- 端点: <路径>

## 部署拓扑
<部署结构描述>

## E2E 测试策略（has_ui: true 时必填）

### Page Object Model 结构
<列出页面/组件及对应的 Page Object 类>

### fixtures 数据准备方案
<测试数据库隔离策略、seed 脚本方案>

### 元素定位策略
<遵循 playwright-standards.md 5 级优先级：getByRole → getByLabel → getByPlaceholder → getByText → getByTestId>

### 测试环境配置
<baseURL、webServer 启动方式、CI 配置>
