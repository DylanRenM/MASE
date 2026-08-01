## Context

当前 `training/mase-framework/` 保存三份 37 页旧版 PPTX 和一份 PDF，但没有可维护的内容事实源或可复现构建方式。旧课件是可编辑文本与矢量形状，并使用深蓝、暖黄、青绿色的 16:9 视觉体系；内容则停留在 v1.x。MASE 的现行规范明确把 training 排除出默认 Agent 上下文，因此课件必须显式引用而不能反向成为工程规则源。

## Goals / Non-Goals

**Goals:**

- 生成一份与 v2.3 现行规则一致、可编辑、可重复构建的 37 页 PPTX。
- 保持 V1 的总体课程结构、逐页职责和视觉语言，只在页内更新已经过时的规则与示例。
- 用中文动作和具体场景先解释概念，再给出必要英文术语。
- 使用结构化内容源分离课程文案与 PPT 绘制逻辑。
- 通过自动测试和 PDF 渲染同时检查语义、结构与视觉可用性。
- 保留旧版文件，以新版本文件名完成非破坏升级。

**Non-Goals:**

- 不把培训课件变成新的规范事实源。
- 不在本 change 更新 AI4SE、Skill 等其他课程。
- 不覆盖或删除 V1 PPTX/PDF，不修改培训大纲 Excel。
- 不承诺所有第三方 PowerPoint 软件像素级一致；以 Microsoft PowerPoint/LibreOffice 可打开、16:9、无越界为底线。
- 不为课件引入网络字体、外部图片或运行时网络依赖。

## Decisions

### 1. 新建 V2.3，而不是原地覆盖 V1

输出文件为 `training/mase-framework/MASE框架培训讲义V2.3.pptx`。旧文件承担历史参考和回滚责任，不进行覆盖或重命名。

### 2. 使用 V1 模板 + YAML 内容源 + Python PPTX 生成器

`MASE框架培训讲义V1.pptx` 作为只读视觉模板，`training/mase-framework/mase-training-v2.3.yaml` 保存 37 页逐页替换内容；`scripts/build_mase_training_deck.py` 校验 V1 checksum 后复制其页面结构并替换可编辑文字。相比重新绘制相似版式，该方案能精确保留 V1 的页面几何、章节节奏、字体、颜色和装饰元素；相比手工修改二进制，内容仍可审查、可测试、可重复生成。

生成器不改变模板形状的坐标、大小或类型，不引用网络资源。模板 checksum 不符、替换目标不存在或页码不连续时直接失败，避免把错误内容静默写入 PPTX。

### 3. 保留 V1 教学骨架，在页内完成 v2.3 升级

37 页继续采用 V1 的六组槽位：定位与理念（1–7）、Agent（8–12）、状态过程（13–22）、项目与工具矩阵（23–24）、逐项工具说明（25–35）、快速上手与总结（36–37）。风险 Profile 放入框架全景和技术预研页；契约、PBT、Capability gate 和候选冻结放入设计、构建、验证与发布页；上下文、Brownfield 和 Sandbox 放入工具与项目组织页。六个 phase 保留熟悉的顺序，但明确为可连续推进的状态标签，不再教成统一重流程或强制审批点。

页面标题以中文为主。例如 “Capability escalation” 改为“能力局部升级”，“Candidate-bound final” 改为“冻结候选再做最终验证”；每个新术语至少给出一个动作、触发条件或具体例子，避免只给定义。

### 4. 规范内容只来自现行运行时文件

课程生成前检查 `framework-manifest.yaml` 版本，并在课件元数据中记录 `source_version: 2.3.0`。核心文案对照 `project-rules.md`、`docs/MASE-framework.md`、`profiles/*.yaml`、`profiles/risks.yaml`、`docs/user-guide.md` 和当前 TDD/PBT Skill。历史博客、`.frontend-slides` 和 V1 只提供视觉与反例参考。

### 5. 自动验证与视觉验证分层

自动验证检查：37 页、16:9、版本、关键主题、禁用旧说法、页码、所有形状在画布内、标题/正文非空、结构化源与输出内容一致。随后用 LibreOffice 无头导出 PDF，再将页面渲染为缩略图接触表，检查文字截断、遮挡、对比度和信息密度。发现问题时修改 YAML 或布局函数后重新生成，而不是手工改 PPTX。

## Risks / Trade-offs

- [37 页内容过密] → 每页限定一个主命题、最多四张卡片和短句，自动检查文本长度并人工看缩略图。
- [中文字体在其他机器替换] → 使用 Aptos/Arial 与苹方/微软雅黑/思源黑体回退，避免依赖下载字体。
- [python-pptx 无法精确检测文字溢出] → 结合字符预算、画布边界检查和 LibreOffice PDF 渲染目视复核。
- [课件再次随框架演进而漂移] → YAML 标注 source_version，验证器与 manifest 版本比较；版本不一致时失败。
- [培训内容被误当规范] → 首页和尾页明确“现行规范以 project-rules/profiles/state/gates 为准”。
- [模板替换破坏 V1 视觉] → 自动比较 37 页全部 shape 的类型与几何；除文字外必须与 V1 一致。
- [术语堆叠导致难懂] → 自动拒绝一组英文抽象标题，并在人工视觉复核时检查“动作/例子/结果”表达。

## Migration Plan

1. 先写验证器与测试，使用不存在/旧版输出取得失败证据。
2. 编写 YAML 内容源与生成器，生成 V2.3 PPTX。
3. 运行自动验证，导出 PDF/缩略图并完成视觉检查。
4. 保留 V1 文件；回滚只需删除新增 V2.3 文件、内容源和脚本。

## Open Questions

无。若后续需要 10 页市场介绍版，可从同一 YAML 选择核心页面另建输出，而不是在本 change 同时维护第二套文案。
