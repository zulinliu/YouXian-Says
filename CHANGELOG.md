# Changelog

本项目的所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2025-05-29

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
