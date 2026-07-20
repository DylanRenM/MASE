# 磨耳朵 macOS MVP Build 验证摘要

> 日期：2026-07-20
>
> 平台：macOS，SwiftPM + Command Line Tools，无完整 Xcode、远端仓库或云端 CI 前置依赖
>
> 结论：Build 门禁 PASS

## 验收包

- 路径：`dist/磨耳朵.app`；
- 版本：`0.1.0 (1)`；最低系统 macOS 13；
- 签名：ad-hoc，`codesign --verify --deep --strict` PASS；
- Info.plist：`plutil -lint` PASS；
- executable size：1,611,600 bytes；
- executable SHA-256：`64703135a9f84ce011f73d913f524ac1339a9c7b3b873ccb09b5c0ac6ad960d9`。

## 自动化门禁

| 门禁 | 结果 |
|------|------|
| Unit | 49/49 PASS |
| Integration | 53/53 PASS |
| Contract | 60/60 PASS |
| Native E2E / infrastructure | 20/20 PASS |
| Proposal P0 | 7/7，100% |
| Proposal P1 | 3/3，100% |
| Release build / bundle / signature | PASS |
| Swift format strict | PASS |
| OpenSpec strict validation | PASS |
| `git diff --check` | PASS |

## 一致性与安全评审

- Spec/contract/architecture：36 条 requirement 与实现/测试证据一致；修正 architecture 中旧 speech 命令名、ReadingClock 描述、bundle 脚本名和 E2E 目录漂移。
- 文件解析：regular/readable/20MB 前置校验；DOCX 只读取 canonical `word/document.xml` 且 50MB 解压上限；PDF 不执行 OCR。
- 路径与归档：外部 URL 均视为不可信；E2E 拒绝临时目录外 sandbox 和 symlink；无 Zip Slip 展开路径。
- 内容：严格 ASCII 英文过滤；E2E 发现并修复不允许字符边界导致的单词粘连；脚本/标记始终作为 inert data。
- 隐私：产品代码无 URLSession/NWConnection/网络 API、无会话持久化、无正文/完整路径日志；E2E release 子进程只注入最小 `LANG` 环境。
- 并发：Swift 6 strict concurrency 编译通过；SessionCoordinator 单串行域；speech/request/session/prompt generation token 隔离迟到回调。

## 已知非阻断提示

测试 runner 链接时提示 `Testing.framework` 构建目标为 macOS 14，而产品 deployment target 为 macOS 13。产品 App 不链接 Testing.framework；release 构建、签名和启动 smoke 均通过，因此不影响 MVP 本地验收。

## 本地交付边界

- 本变更只使用本地 Git；未推送 Gitee、GitHub 或其他远端；
- `.app` 为本机 ad-hoc 签名验收包，不用于公开分发、公证或 App Store；
- 应用重启始终 idle，不持久化文件、播放位置、计时或会话。
