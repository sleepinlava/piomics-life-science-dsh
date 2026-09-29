# 来源声明与许可说明

本目录是基于 `skills/piomics-life-science/` 的 DeepSeek Harness 适配副本。技能目录独立复制，路由技能中的 Pi 专属工具说明已改为宿主中性说明；以下原包来源与授权声明继续适用。本目录不重新许可任何上游内容。

## 1. 上游来源

本包是**二次开发**（derivative adaptation）成果，上游为 OpenAI 的 Life Science Research 插件：

| 项目 | 值 |
|---|---|
| 上游名称 | Life Science Research（Codex 插件） |
| 上游包名 | `life-science-research` |
| 上游版本 | 1.0.3 |
| 上游作者 | OpenAI |
| 上游主页 | https://github.com/openai/openai/tree/master/plugins/life-science-research |
| 上游 manifest | `.codex-plugin/plugin.json` |
| 上游许可声明 | `"license": "Proprietary"` |
| 上游许可文本 | 快照整树未包含任何许可文件 |
| 本地快照 | `PiOmics/skills/life-science-research/`（50 个技能，161 个文件） |
| 快照获取日期 | 快照目录时间戳 2026-09-26；具体下载时间未记录 |

上游快照中唯一的许可证据是 `.codex-plugin/plugin.json` 第 10 行的 `"license": "Proprietary"` 声明；该快照不含 `LICENSE`、`COPYING` 或任何授权文本。仓库既有记录曾据此把该来源标记为 `rights-blocked`（见 `PiOmics/docs/piomics/skill-provenance.md`）。

## 2. 二次开发的范围

本包保留上游 50 个技能的名称、目录层级、科学方法、提示正文与 Python 客户端，改动限于把 Codex 插件形态适配为 Pi 技能包：

| 类别 | 说明 |
|---|---|
| 打包元数据 | 新增 `package.json`（`pi.skills`）、`requirements*.txt`、`provenance.json` 与本文件 |
| 执行环境适配 | 技能正文中的脚本调用改为不依赖当前工作目录，统一使用选定解释器 |
| 路径适配 | 跨技能调用（位点到基因流程）改为按安装位置解析，不再依赖开发机路径 |
| 依赖声明 | 新增 `requests` 等依赖声明；移除要求全局 `pip install` 的指导 |
| 展示适配 | 移除依赖 ChatGPT 图片上传与聊天内联渲染的说明，改为返回产物绝对路径 |
| 文档与验证 | 新增 `README.md`、`docs/runtime.md`、`docs/validation-report.md`、`docs/migration-matrix.csv` |
| 品牌与宿主专属文件 | **未**引入上游 `.codex-plugin/`、`agents/openai.yaml`、图标与任何 OpenAI 品牌标识 |

逐技能的改动结论、未解决问题与验证状态见 `docs/migration-matrix.csv`。

## 3. 授权状态

- 本包维护者于 2026-09-28 声明已取得适配与再分发所需授权，并据此执行了本仓库的迁移（记录见 `provenance.json` 的 `authorization` 字段）。
- 该声明是维护者对授权状态的断言，不改变上游条款；上游声明为 Proprietary 且未提供许可文本。
- 本包 `package.json` 设置 `"private": true`，当前不发布到 npm，仅作本地/内部交付。
- 本包**不**把上游内容重新标注为 MIT 或其他开放许可。

再分发本包或其派生内容时，需自行确认拥有适用授权。上游条款约束上游内容本身。

## 4. 未授予的权利

本文件不构成对上游内容的再许可。上游项目名称、商标与品牌标识归 OpenAI 所有，本包未使用其品牌身份作为本项目的作者身份或标识。

## 5. 联系方式

问题与适配记录请提交到本包的维护渠道；涉及上游技能的科学方法问题应回到上游来源核对。
