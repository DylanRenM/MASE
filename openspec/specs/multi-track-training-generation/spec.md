# multi-track-training-generation Specification

## Purpose
TBD - created by archiving change expand-mase-training-deck. Update Purpose after archive.
## Requirements
### Requirement: 单一培训内容源声明轨道
MASE 培训 YAML SHALL 为每页声明 `core`、`deep-dive` 或 `exercise` 轨道，并 SHALL 以同一内容源生成完整课件，禁止为精简视图复制维护第二套正文。

#### Scenario: 构建完整培训版
- **WHEN** 构建器使用 full 轨道
- **THEN** 输出包含全部 66 页且顺序与 YAML 连续编号一致

#### Scenario: 选择核心轨道
- **WHEN** 构建 API 选择 core 轨道
- **THEN** 系统从同一 YAML 选择对应页面并重新生成连续页码，不读取另一份内容源

### Requirement: 新增页面保持可编辑和模板连续
每个输出页面 SHALL 显式声明受保护 V1 的来源版式，构建器 SHALL 按内容源顺序克隆，而不是把 V1 的 37 页固定在输出前部；页面 MUST 保持文本、形状和流程对象可编辑、Measures 标识存在且所有对象位于 16:9 画布内。

#### Scenario: 克隆四卡片版式
- **WHEN** YAML 页面引用已批准的四卡片模板页
- **THEN** 输出页继承视觉样式，替换后的标题和卡片仍为可编辑文本框

#### Scenario: 深讲页插入基础页之间
- **WHEN** YAML 将一个深讲页排在两个 V1 基础页之间
- **THEN** 输出严格保持该顺序，并分别从三页声明的 `template_slide` 克隆版式

### Requirement: 动态页码和可变页数验证
构建器和验证器 SHALL 从内容源读取期望页数并生成 `NN / TOTAL` 页码，不得将 37 写死在运行逻辑中。

#### Scenario: 生成 66 页课件
- **WHEN** 内容源声明 66 个连续页面
- **THEN** 输出包含 66 页，最后一页页码为 `66 / 66`
