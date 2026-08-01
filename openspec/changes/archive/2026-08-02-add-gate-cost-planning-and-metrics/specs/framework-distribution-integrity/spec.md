## ADDED Requirements

### Requirement: MASE 2.4 版本在分发面一致
MASE SHALL 将 canonical runtime version 设置为 `2.4.0`，并 SHALL 确保 Python 包、Node 元数据、framework manifest、生成模板、文档和当前培训源/课件使用一致的小版本身份。

#### Scenario: 构建 2.4 wheel
- **WHEN** 分发完整性测试检查 wheel 与 manifest
- **THEN** wheel 身份、运行时资源和模板均指向 2.4.0，且不依赖任何采用项目文件
