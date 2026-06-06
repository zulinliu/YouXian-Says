# 贡献指南

感谢您对「攸县有话说」项目的关注！我们欢迎各种形式的贡献。

## 项目简介

「攸县有话说」是一个基于 AI 模型的攸县方言短视频自动化生产系统。在贡献之前，请先阅读 [README](./README.md) 了解项目全貌。

## 许可说明

本项目采用 **CC BY-NC-SA 4.0** 协议发布。请注意：

- **非商业性使用**：贡献的内容不得用于商业目的
- **相同方式共享**：衍生作品必须采用相同的许可协议
- **署名**：必须标注原作者信息

提交贡献即表示您同意您的贡献内容在 CC BY-NC-SA 4.0 协议下发布。

## 如何贡献

### 报告问题

1. 在 [Issues](../../issues) 中搜索是否已有类似问题
2. 如果没有，创建新 Issue，包含：
   - 清晰的问题描述
   - 复现步骤（如适用）
   - 期望行为与实际行为
   - 运行环境信息（Python 版本、操作系统等）

### 提交代码

1. **Fork** 本仓库
2. 基于最新 `main` 分支创建版本迭代分支，命名必须遵循 `feat/vX.Y.Z`：
   ```bash
   git checkout main
   git pull --ff-only origin main
   git checkout -b feat/v1.2.0
   ```
   详细规则见 [分支版本管理与发行版规范](./docs/BRANCHING_AND_RELEASE.md)。
3. 编写代码并确保：
   - 遵循项目现有的代码风格
   - 添加必要的测试
   - 所有现有测试通过
   - 无硬编码的密钥或敏感信息
4. 提交代码，使用清晰的中文提交信息：
   ```bash
   git commit -m "feat: 添加 XXX 功能"
   ```
5. 推送到您的 Fork 并创建 Pull Request

### 版本分支与发行版

- 正式版本分支统一命名为 `feat/vX.Y.Z`，例如 `feat/v0.1.0`、`feat/v0.2.0`、`feat/v1.2.0`。
- 一个版本分支承载一个完整迭代；完成后通过 PR 合入 `main`。
- PR 合入 `main` 后发布同版本 GitHub Release，tag 格式为 `vX.Y.Z`。
- 发布完成后，从最新 `main` 迁出下一个版本分支。
- 完整规范见 [docs/BRANCHING_AND_RELEASE.md](./docs/BRANCHING_AND_RELEASE.md)。

### 提交信息规范

使用以下前缀：

| 前缀 | 用途 |
|------|------|
| `feat:` | 新功能 |
| `fix:` | 修复 Bug |
| `refactor:` | 代码重构 |
| `docs:` | 文档更新 |
| `test:` | 测试相关 |
| `chore:` | 构建/工具变更 |
| `perf:` | 性能优化 |

### 贡献攸县方言内容

我们特别欢迎以下内容的贡献：

- **方言词汇**：扩充 `data/dialect_dict.json` 中的攸县方言词典
- **知识库**：完善 `data/knowledge_base.md` 中的攸县地方知识
- **语料数据**：提供规范的方言语音或文本语料（需确保版权清晰）

## 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/your-username/YouXian-Says.git
cd YouXian-Says

# 一键安装
bash scripts/setup.sh

# 激活环境
source venv/bin/activate

# 运行测试
pytest tests/ -q -m "not api and not slow"
```

## 代码规范

- Python 3.11+，遵循 PEP 8
- 所有函数添加类型注解
- 使用 `black` 格式化、`ruff` 检查
- 函数不超过 50 行，文件不超过 800 行

## 安全注意事项

- **禁止**提交 API Key、密码等敏感信息
- 敏感配置通过 `.env` 文件管理（已加入 `.gitignore`）
- 如发现安全漏洞，请按照 [SECURITY.md](./SECURITY.md) 中的流程报告

## 行为准则

参与本项目即表示您同意遵守我们的 [行为准则](./CODE_OF_CONDUCT.md)。

## 问题与讨论

如有任何疑问，欢迎通过 [Issues](../../issues) 或 [Discussions](../../discussions) 与我们交流。
