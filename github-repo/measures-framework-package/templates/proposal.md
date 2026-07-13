---
change: "<change-name>"
created: "YYYY-MM-DD"
agent: "agent-2-requirements"
---

## Why
<为什么做这个变更？解决什么问题？>

## What Changes
<变更的具体内容，按功能模块描述>

## Capabilities

### New Capabilities
- `<capability-name>`: <一句话描述>

### Modified Capabilities
- `<capability-name>`: <修改内容>

## Impact
- 技术依赖: <需要什么基础设施>
- 存储: <存储需求>
- 性能: <性能影响>
- 外部依赖: <外部 API/服务>

## Out of Scope
- <明确不做的事>

## Stakeholders
- <干系人列表>

## Success Criteria
- [ ] <成功标准1>
- [ ] <成功标准2>

## 操作流程
1. <步骤1>
2. <步骤2>
...

## 系统测试用例
| 用例ID | 前置条件 | 操作步骤 | 预期结果 |
|--------|---------|---------|---------|
| TC-001 | <前置> | <操作> | <预期> |

## E2E 验收场景（has_ui: true 时必填）

> P0 = 核心业务流程，必须 100% E2E 覆盖。
> P1 = 重要辅助功能，应当覆盖。
> P2 = 边缘场景，可人工探索。

### 场景 1: <场景名称>
- 用户故事: 作为<角色>，我希望<操作>，以便<价值>
- 前置条件: <条件>
- 操作步骤:
  1. <步骤>
  2. <步骤>
- 预期结果: <可验证的断言>
- 优先级: P0（核心）/ P1（重要）/ P2（次要） |
