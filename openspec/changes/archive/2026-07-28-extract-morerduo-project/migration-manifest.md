# 磨耳朵仓库迁移清单

## 来源与目标

- Source root: `/Users/dylanren/Documents/trae_projects/MASE`
- Source branch: `feat/adaptive-lightweight-mase`
- Source commit: `a28c4f61fcb963022cc84f9bb250f9114ea2b7d5`
- Target root: `/Users/dylanren/Documents/trae_projects/磨耳朵`
- Repository mode: independent local Git; no remote

## 跟踪产品文件

| 路径 | 数量 |
|---|---:|
| Package.swift / Package.resolved | 2 |
| src | 85 |
| resources | 1 |
| docs/codes-projects/磨耳朵 | 7 |
| openspec/master | 12 |
| openspec/changes/macos-english-listening-mvp | 31 |
| scripts/build-morerduo-app.sh / verify-morerduo.sh | 2 |
| tests/unit | 16 |
| tests/integration | 17 |
| tests/contract | 22 |
| tests/support | 3 |
| tests/e2e Swift product files | 12 |
| **合计** | **210** |

`tests/e2e/sandbox.test.js` 明确归 MASE 框架，不计入产品。

## 校验基线

- Aggregate tracked product SHA-256: `bbf6f2d3ddb720de9b0d07b0f1bb09812d32eb6a70bcfa55b90a2653a4f4925b`
- Package.swift: `87bbd6c60ffb8935bcb70c10412744a7e5712a2fe7576fbb5856363c4cbcd8d6`
- Package.resolved: `86b5d92b0d323fda8d7be2793fe4015a3dcf28f1f0d996e3749e804d92a47742`
- verify script: `a1968b0bcb4f21098b855c7ddd8ea136e97c623d438241daf26716f8ef2e9761`
- accepted app executable: `64703135a9f84ce011f73d913f524ac1339a9c7b3b873ccb09b5c0ac6ad960d9`

## 生成物与空间

- Root `.build`: 1.1GB — move, not copy.
- POC `.build`: 846MB — do not migrate; delete only after target verification.
- `dist`: 1.6MB — move with accepted app.

## 迁移前验收

- Unit 49/49
- Integration 53/53
- Contract 60/60
- Native E2E 20/20
- Release build, app bundle and ad-hoc signature PASS

## 迁移后结果

- Target branch: `main`
- Import commit: `3d56e5a feat: import accepted macOS MVP`
- Migration portability fix: `d64768e fix: make verification portable after repository move`
- Final evidence commit: `45510d1 docs: update migration verification evidence`
- 209 个未修改产品文件逐文件 SHA-256 比对：0 mismatch；迁移中按新边界调整的文件另行提交并验收。
- Unit 49/49, Integration 55/55, Contract 60/60, Native E2E 20/20 PASS.
- Release build, `dist/磨耳朵.app`, plist, ad-hoc signature and Accessibility smoke PASS.
- Target Git worktree clean; no external remote.
- MASE root `.build` absent; POC `.build` deleted after target verification.
