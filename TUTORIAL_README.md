# 教程生成使用说明（当前版本）

当前项目的教程产出完全由 **离线脚本** 驱动。默认 UI 不再展示、下载或触发教程生成。如需对接，请参考以下说明了解输入、输出及可复用的接口。

---

## 1. 流程概览

```
需求方给出教程主题 → 运行 launch_planning.py（离线） → 输出 FULL_TUTORIAL.ipynb
→ 将 Notebook 提供给使用方（复制文件或自建接口分发）
```

| 角色 | 输入 | 输出 |
|------|------|------|
| 脚本执行者 | 如 `--text-input "教程主题"` 等参数 | `output/FULL_TUTORIAL.ipynb` |
| 前端/其它系统 | 读取 `output/` 下的 Notebook 文件 | 自行渲染或下载 |

---

## 2. 生成脚本与参数

### 示例命令

```bash
python launch_planning.py \
  --text-input "请生成 Vision Transformer 教程" \
  --output_dir ./output \
  --non_interactive \
  --skip_literature_summary \
  --auto_survey \
  --enable_review
```

### 参数对照

| 参数 | 含义 | 默认/备注 |
|------|------|-----------|
| `--text-input` | 教程需求描述 | 必填 |
| `--output_dir` | Notebook 输出目录 | `./output` |
| `--non_interactive` | 自动模式，无需人工确认 | 建议开启 |
| `--skip_literature_summary` | 跳过文献总结 | 当前教程默认不做文献环节，请显式添加 |
| `--auto_survey` | 自动执行调研模块 | 若完全不做调研，可移除此参数并确保流程不依赖调研 |
| `--enable_review` | 启用双审稿流程 | 默认关闭，推荐开启 |
| `--max_papers` | 调研阶段论文上限 | 20 |
| `--max_rounds` | 规划/调研迭代次数上限 | 3 |
| `--enable_judger` | 是否启用计划打分 | 默认 `False` |
| `--target_audience` | 教程受众（如 `beginners`） | `beginners` |
| `--max_revision_rounds` | 审稿允许的最大修改轮数 | 2 |
| `--min_clarity_score` / `--min_coherence_score` | 审稿通过最低分 | 7.5 |

执行完成后，`output/` 目录会包含：

- `FULL_TUTORIAL.ipynb`（完整教程）
- `iterations/` 目录（调研、审稿等中间记录，可选）

---

## 3. 教程交付方式

### 3.1 直接交付（推荐）

- 将 `output/FULL_TUTORIAL.ipynb` 复制给需求方或上传到内部文档系统。
- 使用方可在 Jupyter Notebook、VS Code、nbviewer 等工具中打开。

### 3.2 可复用接口（如需自建前端）

- 仍保留 `GET /api/tutorial/full`：
  - `path`（可选）：指定 `output/` 下其他 Notebook
  - 返回：`{ success, path, notebook, message? }`
- 默认 UI 未使用该接口；如要集成，可自行请求并渲染。

> `/api/tutorial/generate`、`/api/tutorial/status/*` 等在线生成功能已下线，如需恢复需重新启用服务并补齐权限控制。

---

## 4. 在其它系统中展示的思路

1. **获取 Notebook**：直接访问服务器文件，或调用 `/api/tutorial/full`。
2. **渲染方式**：
   - 简单：提取部分 Markdown/代码作为摘要。
   - 完整：使用 nbviewer、`nbconvert` 或自定义渲染器。
3. **下载**：`JSON.stringify(notebook)` → `Blob` → `URL.createObjectURL`，即可提供下载链接。

---

## 5. 常见问题

| 问题 | 处理方式 |
|------|----------|
| 找不到 `FULL_TUTORIAL.ipynb` | 检查 `--output_dir`，确认脚本执行成功 |
| Notebook 打不开/内容为空 | 查看脚本日志，必要时重新生成或恢复备份 |
| 需要多个教程版本 | 在 `output/` 下按任务建子目录，例如 `output/vit/FULL_TUTORIAL.ipynb` |
| 想恢复在线生成 | 需重新启用 `tutorial_generation_service` 及相关接口，并在前端加输入表单与状态轮询 |

---

如需扩展新的接口或上线前端展示，请以此文档为基础补充清晰的输入/输出说明，保证所有对接方信息一致。 
# 教程生成使用说明（前端 & 产品对接）

本文档解释：**前端输入什么 → 如何触发/读取 → 能拿到什么输出**，以便快速对接本项目的“教程生成”能力。

---

## 1. 整体流程

```
用户或运营 → 输入教程需求（文本）
        ↓
研究脚本（launch_planning.py 等）离线运行 → 生成 FULL_TUTORIAL.ipynb
        ↓
后端暴露 /api/tutorial/full → 提供 Notebook JSON
        ↓
前端调用接口 → 展示摘要 + 下载 Notebook
```

### 角色输入输出
| 角色 | 输入 | 输出 |
|------|------|------|
| **脚本/后台** | `--text-input "教程主题"` 等参数 | `output/FULL_TUTORIAL.ipynb` |
| **后端 API** | `GET /api/tutorial/full (?path=...)` | Jupyter Notebook JSON |
| **前端** | API 返回的 `notebook` | 页面预览 & 下载按钮 |

---

## 2. 生成脚本（离线执行）

### 示例命令
```bash
python launch_planning.py \
  --text-input "请生成 Vision Transformer 教程" \
  --output_dir ./output \
  --non_interactive \
  --skip_literature_summary \
  --auto_survey \
  --enable_review
```

| 参数 | 说明 |
|------|------|
| `--text-input` | 用户的教程需求描述（必填） |
| `--output_dir` | Notebook 输出目录，默认 `./output` |
| `--non_interactive` | 以“自动模式”运行，不需要人工确认 |
| `--skip_literature_summary` | 跳过文献总结与引用整理。本项目默认不开启文献调研，因此需要显式加上 |
| `--auto_survey` | 自动执行调研阶段（即便无人工交互）；若完全不希望跑调研，可移除该参数并确保 pipeline 不依赖调研输出 |
| `--enable_review` | 启用教程双审稿流程（Pedagogical + Logical reviewers） |
| 常用补充参数 | 说明（默认值按 `launch_planning.py` 中设置） |
| `--max_papers` | 调研阶段最多读取的论文数量；默认 20 |
| `--max_rounds` | 规划/调研允许的最大迭代轮次；默认 3 |
| `--enable_judger` | 是否启用计划打分（JudgerAgent）；默认关闭 |
| `--target_audience` | 指定教程面向的人群（如 `beginners`、`intermediate`）；默认 `beginners` |
| `--max_revision_rounds` | 审稿允许的最大修改轮数；默认 2 |
| `--min_clarity_score` / `--min_coherence_score` | 评审通过的最低分要求；默认分别为 7.5 |

执行完成后，`output/FULL_TUTORIAL.ipynb` 即为最终教程。前端不需要知道脚本细节，但需确保该文件存在。

---

## 3. 后端接口（供前端调用）

### `/api/tutorial/full`

- **Method**：`GET`
- **输入（Query）**：
  | 参数 | 类型 | 说明 | 必填 |
  |------|------|------|------|
  | `path` | string | 可选，指向 `output/` 下的其它 `*.ipynb`（默认 `FULL_TUTORIAL.ipynb`） | 否 |
- **输出（JSON）**：
  | 字段 | 类型 | 说明 |
  |------|------|------|
  | `success` | bool | 是否成功 |
  | `path` | string | 实际返回的 notebook 绝对路径 |
  | `notebook` | object | Jupyter Notebook JSON（含 `cells` 等全部内容） |
  | `message` | string | 失败时的错误提示 |

```bash
curl -X GET "http://<host>:5000/api/tutorial/full" -H "Accept: application/json"
```

> 当前服务只暴露“读取”接口；`/api/tutorial/generate` 等在线生成接口已下线，如需恢复需重新上线。

---

## 4. 前端对接要点

### 4.1 DOM 节点
| 节点 | 功能 |
|------|------|
| `#loadTutorialBtn` | 触发接口调用 |
| `#tutorialViewerStatus` | 显示状态提示 |
| `#tutorialViewerContent` | 展示前几段摘要 |
| `#downloadTutorialLink` | 下载 Notebook |

### 4.2 JS 逻辑（`app.js`）
| 函数 | 作用 |
|------|------|
| `fetchTutorialNotebook()` | 调接口、处理响应/错误 |
| `renderTutorialPreview(notebook)` | 取前 6 个 cells 渲染 |
| `setTutorialStatus(message)` | 更新状态文本 |

### 4.3 下载流程
1. `JSON.stringify(notebook)` → `Blob`
2. `URL.createObjectURL(blob)` → 赋值给下载链接
3. 再次加载前 `URL.revokeObjectURL` 释放旧链接

---

## 5. 典型使用场景

1. **运营/研发**：在后端服务器运行脚本，生成 `output/FULL_TUTORIAL.ipynb`
2. **前端**：点击“读取教程”按钮 → `GET /api/tutorial/full`
3. **用户**：在页面上查看预览或点击“下载 Notebook”

若提供多个教程版本，只需将对应 `.ipynb` 放在 `output/` 下，前端调用时传 `?path=xxx.ipynb`。

---

## 6. 常见问题

| 问题 | 可能原因 | 处理 |
|------|----------|------|
| “未找到教程文件” | 输出目录没有 `FULL_TUTORIAL.ipynb` | 重新生成或确认路径 |
| 预览/下载为空 | Notebook JSON 损坏或文件为空 | 检查文件体积，必要时重新生成 |
| 想在线输入问题→直接生成 | 需恢复 `/api/tutorial/generate`、`/api/tutorial/status` 等接口，并在前端加表单与状态轮询 |

---

## 7. 扩展建议

1. **在线生成**：重新启用 `tutorial_generation_service` + 前端输入框；
2. **多版本列表**：提供下拉菜单，让用户选择不同的 `path`;
3. **富预览**：用 nbviewer 或 markdown 渲染库展示完整 Notebook；
4. **发布流程**：后台生成后，可通过 CI/脚本自动拷贝到 `output/`，前端无需改动。

---

如需恢复自动生成或新增接口，请与后端协作并在本说明基础上补充对应输入/输出。 

