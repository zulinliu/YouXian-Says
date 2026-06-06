# Changelog

本项目的所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.0] - 2026-05-29

### Changed

- 前端深度重构：浅色简约设计系统替代暗色主题，统一 CSS Token 体系
- 登录页重设计：渐变背景、无边框圆角卡片、输入框 focus 状态、按钮 hover 动效、淡入动画
- 侧边栏重设计：品牌 Logo 区域、导航图标（Remix Icon）、活动项粉色高亮
- 新增工作台首页（workspace）：待办任务看板、视频生产流水线、本周概览统计
- 选题共创页： Remix Icon 图标、流水线进度条、DB 持久化、跨页面导航
- 视频审核页：状态机对接 FastAPI、审核反馈 DB 存储、快速审核模式
- 发布中心页：平台图标（抖音/微信）、发布队列、定时发布
- 数据洞察页：指标卡片、空数据引导、周报结构化展示
- 系统设置页：视频生命周期追踪移入工作台、模型连接测试

### Added

- 分支版本管理与发行版规范（`docs/BRANCHING_AND_RELEASE.md`），约定 `feat/vX.Y.Z`、PR 合入 `main`、发布 `vX.Y.Z` 发行版、发布后迁出下一版本分支

- `web/styles.py` — 全局 CSS 注入模块：设计 Token、Remix Icon、共享 UI 组件
- `web/pages/workspace.py` — 工作台首页
- `.streamlit/config.toml` — Streamlit 全局主题配置
- Remix Icon 4.6.0 CDN 集成，全站零 emoji
- CSS "攸" SVG Logo（登录页 72px / 侧边栏 36px）
- Cookie 持久化认证（解决刷新/导航丢失 session）
- 移动端响应式适配（iOS Safari / Android Chrome）

### Fixed

- 侧边栏折叠后无展开按钮（stToolbar display:none 误杀 stExpandSidebarButton）
- 登录页密码框 "press enter to apply" 提示（st.form 包裹）
- 侧边栏刷新后消失（Cookie JWT 恢复认证状态）
- XSS 漏洞修复（HTML 转义所有变量内容）

## [1.0.0] - 2026-05-29

### Added

- 选题共创：基于 LLM 的攸县方言短视频选题生成，支持热点追踪与话题挖掘
- 脚本撰写：方言文化类、生活日常类等多种脚本模板，自动生成攸县方言台词
- 语音合成：集成 MiniMax、MiMo 等语音引擎，支持方言语音克隆
- 数字人口播：HeyGen 数字人集成，支持自定义形象
- 视频合成：B-roll 素材自动生成（Kling/Runway），FFmpeg 智能合成
- Web 后台：Streamlit 多页面管理界面（选题、审核、发布、数据看板、模型设置）
- FastAPI 后端：RESTful API，JWT 认证，SQLite 数据存储
- 多模型路由：DeepSeek、MiniMax、MiMo、OpenAI Relay 等多模型统一调度
- 模型横评：文本、语音、图像、视频、数字人五大维度评估框架
- 数据加密：Fernet 对称加密保护敏感配置
- 完整的 GitHub 社区规范：Issue 模板、PR 模板、行为准则、安全策略、贡献指南

### Security

- JWT 认证密钥与管理员密码分离
- hmac.compare_digest 防止时序攻击
- 状态机校验防止非法状态转换
- 环境变量统一管理，杜绝硬编码密钥
