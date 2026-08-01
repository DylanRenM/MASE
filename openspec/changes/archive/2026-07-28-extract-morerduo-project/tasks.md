## 1. 迁移清单与恢复边界

- [x] 1.1 生成产品归属清单，区分磨耳朵跟踪文件、MASE Sandbox 测试和大型生成缓存
- [x] 1.2 记录来源分支/提交、目标路径、文件数、关键哈希和迁移前验证结果

## 2. 建立独立磨耳朵仓库

- [x] 2.1 创建平级目标目录并复制 Package、源码、资源、产品测试、需求、OpenSpec 和脚本
- [x] 2.2 添加独立 README、Gitignore、MASE v2 Standard/Swift 元数据与 generated IDE adapters
- [x] 2.3 移动 dist 和根 `.build`，排除 POC `.build`，并验证目标文件清单与哈希
- [x] 2.4 初始化独立本地 Git 并创建带来源 provenance 的首次提交

## 3. 新目录产品验证

- [x] 3.1 在新目录运行 Unit、Integration、Contract、Native E2E、release build、bundle 和签名全套验证
- [x] 3.2 确认新目录验收包、OpenSpec 状态和 Git 工作树完整一致

## 4. 清理 MASE 产品耦合

- [x] 4.1 将 Sandbox JavaScript 测试迁入 MASE 框架测试目录并更新 Vitest 配置
- [x] 4.2 从 MASE 删除全部磨耳朵跟踪路径、产品 dist 与 POC 构建缓存
- [x] 4.3 更新 MASE manifest、generic check 和文档，删除产品实例专属排除和结构假设

## 5. 双仓库门禁与提交

- [x] 5.1 运行 MASE Python、Sandbox JS、OpenSpec strict、规则同步、compile 和 `mase check`
- [x] 5.2 验证两个 Git 根平级独立、MASE 不含产品文件、磨耳朵不含框架运行时
- [x] 5.3 更新迁移 change 状态与验证摘要，在 MASE 创建本地拆分提交
