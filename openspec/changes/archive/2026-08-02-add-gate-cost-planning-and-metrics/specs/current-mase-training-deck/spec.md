## ADDED Requirements

### Requirement: 2.4 课件融合讲解风险自适应验证
可编辑 MASE 2.4 课件 SHALL 在原有相关章节中融合讲解验证里程碑、Change Risk L1–L4、UI 三分类、OpenSpec Lite、Gate DAG、精确缓存和成本指标，并 SHALL 保持六步开发主线与六项独立原则。

#### Scenario: 学员按课程顺序阅读
- **WHEN** 学员从原则、角色、六步开发主线进入测试、门禁、证据和度量章节
- **THEN** 每项 2.4 能力出现在其概念首次需要的位置，而不是集中追加为附录

### Requirement: 2.4 课件保持可编辑与 V1 保护
系统 SHALL 从版本化结构源生成 16:9 可编辑 `MASE框架培训讲义V2.4.pptx`，并 MUST 保持受保护 V1 文件字节摘要不变。

#### Scenario: 生成并验证课件
- **WHEN** 构建脚本生成 2.4 PPTX
- **THEN** 文本和形状可编辑、无越界，V1 SHA 与受保护值一致
