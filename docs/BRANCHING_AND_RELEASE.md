# 分支版本管理与发行版规范

本规范是项目长期记忆的一部分，适用于「攸县有话说」后续所有版本迭代、PR 合并与发行版发布。

## 1. 分支模型

| 分支类型 | 命名 | 用途 | 合并规则 |
|----------|------|------|----------|
| 主干分支 | `main` | 唯一稳定发布线；每次合入代表可发布版本 | 禁止直接开发提交，只接受版本分支 PR |
| 版本迭代分支 | `feat/vX.Y.Z` | 承载一个完整版本迭代，例如 `feat/v0.1.0`、`feat/v0.2.0`、`feat/v1.2.0` | 完成验收后通过 PR 合入 `main` |
| 临时试验分支 | `spike/<topic>` 或 `tmp/<topic>` | 短期验证，不承载正式版本 | 不直接合入 `main`；需整理进版本分支 |
| 历史归档分支 | `archive/<topic>` | 仅保留旧历史或废弃路线 | 不直接合入 `main`；如需复用，cherry-pick 到版本分支 |

**强制约定：**

- 正式版本分支统一使用 `feat/vX.Y.Z`，其中 `X.Y.Z` 遵循语义化版本。
- 不再使用 `feat/v1`、`feat/v2` 这类里程碑简写。
- 不再新建 `feature/<name>` 作为长期开发分支；需求应归入当前版本分支。
- 如果误建了 `feat/X.Y.Z`（缺少 `v`），应立即重命名为 `feat/vX.Y.Z`。

## 2. 语义化版本规则

版本号格式：`MAJOR.MINOR.PATCH`。

| 版本段 | 递增场景 | 示例 |
|--------|----------|------|
| `MAJOR` | 破坏性架构变化、数据结构不兼容、产品形态大改 | `v1.9.0` → `v2.0.0` |
| `MINOR` | 一个完整功能迭代、页面/流程升级、新模块上线 | `v1.1.0` → `v1.2.0` |
| `PATCH` | Bug 修复、安全修复、小范围文档或配置修正 | `v1.2.0` → `v1.2.1` |

早期版本可以从 `v0.1.0`、`v0.2.0` 开始；本项目现有历史已使用 `v1.0.0` 作为 MVP 版本，因此后续沿用 `v1.x.x`。

## 3. 创建版本分支

每个新版本必须从最新 `main` 创建：

```bash
git checkout main
git pull --ff-only origin main
git checkout -b feat/vX.Y.Z
git push -u origin feat/vX.Y.Z
```

创建后在 `.planning/STATE.md` 记录当前版本号、目标和状态。

## 4. 迭代期间约定

- 提交信息使用 Conventional Commits 前缀：`feat:`、`fix:`、`docs:`、`refactor:`、`test:`、`chore:`、`perf:`。
- 版本分支内允许多个提交，但必须保持可追溯、可回滚。
- 涉及需求、架构、流程、发布规范的变更，必须同步更新 `.planning/` 或 `docs/` 文档。
- 敏感信息（API Key、账号、Cookie、密码）不得提交。

## 5. 合并到 main 前检查

版本分支完成迭代后，创建 PR 到 `main` 前必须完成：

```bash
git status --short
ruff check . --ignore E501
pytest tests/ --tb=short -q -m "not api and not slow"
```

同时确认：

- 工作区干净，无暂存、未提交或未跟踪的发布相关文件。
- `CHANGELOG.md` 包含目标版本变更摘要。
- `pyproject.toml` 中版本号与目标发行版一致。
- `.planning/STATE.md` 已记录该版本完成状态。
- PR 标题建议使用：`release: vX.Y.Z <版本摘要>`。

## 6. PR 合并规则

- 版本分支完成后，通过 PR 合入 `main`。
- 默认保留版本分支提交历史，避免 Squash 后丢失 release-please / changelog 可识别的 Conventional Commits。
- 禁止跳过 PR 直接向 `main` 推送业务代码。
- PR 合并后，`main` 必须是可运行、可测试、可发布状态。

## 7. 发行版发布

PR 合入 `main` 后发布对应发行版：

1. 确认 `main` 已同步：
   ```bash
   git checkout main
   git pull --ff-only origin main
   ```
2. 确认版本号：
   ```bash
   grep -n "version" pyproject.toml
   ```
3. 使用 tag 格式 `vX.Y.Z` 发布：
   ```bash
   git tag -a vX.Y.Z -m "release: vX.Y.Z"
   git push origin vX.Y.Z
   ```
4. 在 GitHub Release 中使用 `CHANGELOG.md` 对应版本内容作为发行说明。

本仓库已配置 `Release Please` 工作流监听 `main`。如使用自动发布，以 `Release Please` 生成/合并的 release PR 与 GitHub Release 为准；如需手动发布，必须保持 tag、`CHANGELOG.md`、`pyproject.toml` 三者版本一致。

## 8. 发布后迁出下一版本分支

当前版本发布完成后，立即从最新 `main` 迁出下一版本分支：

```bash
git checkout main
git pull --ff-only origin main
git checkout -b feat/vNEXT
git push -u origin feat/vNEXT
```

示例：`v1.1.0` 发布后，下一个功能迭代分支为 `feat/v1.2.0`。

## 9. 当前历史分支迁移记录

| 历史分支 | 规范分支 | 对应发行版 | 状态 |
|----------|----------|------------|------|
| `feat/v1` | `feat/v1.0.0` | `v1.0.0` | MVP 完成分支 |
| `feat/v2` | `feat/v1.1.0` | `v1.1.0` | 前端深度重构完成分支 |
| `feature/liuzl` | `archive/feature-liuzl` | 不单独发行 | 旧开发历史归档，仅供追溯 |

迁移完成后，新迭代从 `feat/v1.2.0` 开始。

## 10. 项目记忆

该规范为永久项目约定：后续所有分支命名、PR 合并、发行版发布、下一版本迁出，都必须遵循本文件。若规范需要调整，必须同时更新：

- `docs/BRANCHING_AND_RELEASE.md`
- `CONTRIBUTING.md`
- `.planning/PROJECT.md`
- `.planning/STATE.md`
