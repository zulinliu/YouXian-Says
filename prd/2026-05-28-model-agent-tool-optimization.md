# 攸县方言短视频系统 - 模型、Agent、工具优化方案

> 版本日期：2026-05-28  
> 状态：已通过评审  
> 适用文档：`2026-05-28-youxian-dialect-video-design.md`、`2026-05-28-youxian-tech-spec.md`  
> 结论性质：结合你已购模型、你的新增约束、官方资料检索和短视频生产场景推导。最终上线前必须用本项目样例集盲测确认。

## 0.1 评审后的修订决策（2026-05-28）

本优化方案按用户最新确认做以下收敛：

| 项目 | 修订后策略 |
|---|---|
| MVP节奏 | 先每周3条，优先抖音和视频号；稳定后再扩四平台日更 |
| 数字人 | 先虚拟本地人设；HeyGen/Tavus/D-ID/AKOOL 先做接口预留，系统稳定后再采购小额验证 |
| B-roll视频 | Runway/Veo/Kling/Luma/Pika 仍是优先候选，但不立即购买；先完成适配器、配置项、Mock/占位素材流程 |
| 声音 | 先本人声音克隆；其他人声音克隆只在后续明确授权后扩展 |
| 历史/风俗事实 | 爆款共创优先，来源检索作为质量护栏和风险分级，不作为所有内容的硬阻塞 |
| 发布 | MVP默认发布前用户确认，稳定后再开放无人值守 |
---

## 一、核心结论

短视频系统不能按“一个能力只选一个模型”设计。更合理的方式是：按任务场景路由，低成本模型负责批量草稿，高质量模型负责关键定稿，媒体模型按效果/成本/稳定性分层，所有调用进入日志和横评体系。MVP阶段不立即采购新增媒体模型，先搭建路由、适配器、配置和占位流程，系统稳定后再小额验证。

| 场景层级 | 默认优先级 | 说明 |
|----------|------------|------|
| 批量草稿层 | DeepSeek V4 Flash、MiMo V2.5、GLM-5.1 轻量调用 | 选题池、标题池、标签、脚本初稿、日报，追求低成本和高吞吐；MiniMax M2.7 只保留为基线对照。 |
| 深度推理层 | **GLM-5.1 > GPT-5.5 > DeepSeek V4 Pro** | 复杂策略、方案评审、脚本结构诊断、异常归因、技术设计。按你指定顺序执行。 |
| 中文口语润色层 | MiMo V2.5 Pro、GLM-5.1、GPT-5.5 | 口播节奏、短句化、语气自然度、素材质检；MiniMax M2.7 只在前述模型不可用或盲测胜出时启用。 |
| 图像生产层 | **GPT-image-2 > Firefly/Imagen/Seedream/FLUX 横评 > MiniMax image-01** | 图片素材主要靠网络搜索和 AI 生成，且你实测 `gpt-image-2` 效果最好，因此设为主线；MiniMax image-01 不再做直接第二选择。 |
| 语音生产层 | **MiMo VoiceClone/VoiceDesign/TTS > ElevenLabs > Cartesia > OpenAI TTS > MiniMax Speech 2.8** | 先用已购小米官方语音能力；若方言咬字或情绪不足，外部高质量语音 API 优先于 MiniMax。 |
| 视频 B-roll 层 | Runway Gen-4 Turbo > Veo 3.1 Lite/Fast > Kling > Luma/Pika > Hailuo-2.3/2.3-Fast | 不按国内外划分，按短视频 B-roll 的可用率、成本、API、9:16 适配排序；Hailuo 因你反馈效果弱，降为兜底/基线。 |
| 数字人口播层 | HeyGen > Tavus > D-ID > AKOOL > Synthesia/腾讯智影/剪映数字人 | 主目标是“稳定 30-90 秒口播 + 口型同步 + API/半自动可落地”。 |

中转站模型不再按通道来源一刀切降级。你说明这些模型通过 New API 中转，效果基本接近官方，因此技术方案应把它们定义为 `channel=new_api_relay`：可进入主链路，但需要单独监控稳定性、延迟、计费、上下文、工具调用、图片/文件上传差异和数据合规策略。

**MiniMax 全局降级规则：** 因你已明确 MiniMax 相关模型当前效果相对不高，本文档把 MiniMax 全系列（M2.7、Speech 2.8、image-01、Hailuo、Music 2.6）统一降级为“已购兜底/基线对照/无更优方案时临时使用”。除非在本项目样例盲测中显著胜出，MiniMax 不进入任一主生产链路的第一、第二优先级。

---

## 二、检索后的模型理解

### 2.1 图像：GPT-image-2 应作为主线

OpenAI 官方文档把 `gpt-image-2` 定位为最高性能的图像生成模型，支持文本和图像输入、图像输出、图像生成与编辑端点，适合高质量封面、分镜参考图、历史场景复原、美食/街景氛围图生成。本项目没有稳定实拍图来源，且你已明确 `gpt-image-2` 当前效果最满意，因此不应再把 MiniMax image-01 放在图像主线。

推荐：
- 主线：`gpt-image-2`，用于封面、主视觉、分镜参考图、缺失实景补图。
- 第一候选横评：Adobe Firefly / Google Imagen / Seedream / FLUX，用于版权、中文场景、风格一致性或平台限制需要时对比。
- 最后兜底：`MiniMax image-01`，仅用于中转站不可用、外部候选不可用、批量低风险草图或样例盲测胜出。

来源：[OpenAI GPT Image 2 Model](https://developers.openai.com/api/docs/models/gpt-image-2)

### 2.2 语音：先小米，再外部优质服务，MiniMax 最后兜底

小米 MiMo 已购语音模型覆盖 `mimo-v2.5-tts-voiceclone`、`mimo-v2.5-tts-voicedesign`、`mimo-v2.5-tts`，更符合你“优先小米”的约束。ElevenLabs、Cartesia、OpenAI TTS 都有公开 API/价格文档，适合作为小米效果不足时的小额横评池。MiniMax Speech 2.8 虽覆盖 TTS、长文本语音、声音克隆和声音设计，但结合你的实测反馈，只保留为最后兜底和基线对照。

推荐优先级：

| 优先级 | 模型/服务 | 用法 |
|--------|-----------|------|
| P0 | MiMo V2.5 TTS VoiceClone | 主配音首选，验证攸县方言咬字、音色相似度、稳定性。 |
| P0 | MiMo V2.5 TTS VoiceDesign | 角色声线、旁白风格、非本人克隆声线。 |
| P1 | MiMo V2.5 TTS | 普通旁白、低成本批量版本。 |
| P1 | ElevenLabs Multilingual / Flash-Turbo | 中文普通话、情绪和克隆效果强，需实测攸县方言；小额优先横评。 |
| P2 | Cartesia Sonic-3 | 低延迟和实时语音强，若后续做互动 Agent 优先级上升。 |
| P3 | OpenAI TTS | 普通旁白、标准普通话和稳定 API 兜底，不作为方言克隆主线。 |
| P4 | MiniMax Speech 2.8 HD/Turbo | 已购但不优先；仅小米与外部候选不可用、成本异常或样例盲测胜出时启用。 |

不考虑本地开源训练路线作为 MVP 主路，因为你没有 GPU 资源；只保留“外部托管 API/云端服务”作为未来候选。

来源：[MiMo 语音合成文档](https://platform.xiaomimimo.com/docs/usage-guide/speech-synthesis-v2.5)、[ElevenLabs API Pricing](https://elevenlabs.io/pricing/api)、[Cartesia Pricing](https://cartesia.ai/pricing)、[OpenAI TTS 文档](https://platform.openai.com/docs/guides/text-to-speech)、[MiniMax API Overview](https://platform.minimax.io/docs/api-reference/api-overview)

### 2.3 深度推理：按用户指定顺序路由

深度推理类任务不等于所有文本任务。批量低风险文本仍应使用 DeepSeek Flash、MiMo V2.5 等低成本模型；真正需要复杂推理时，按以下顺序：

1. `glm-5.1`
2. `gpt-5.5`
3. `deepseek-v4-pro`

适用任务：
- 选题策略和赛道判断。
- 脚本结构问题诊断。
- 多平台数据归因。
- 模型/Agent/工具方案评审。
- 技术架构和异常处理方案。
- 高风险内容的合规和反方推理。

DeepSeek V4 Pro 仍是稳定中文生产模型，但在“深度推理”这个专业场景里退到第三顺位。

### 2.4 视频：全球候选，按效果成本比排序

视频模型不应只看已购，也不应只看国内外。短视频 B-roll 的关键指标是：9:16 适配、单条成本、API/批量能力、中文提示词理解、画面可用率、人物/食物/街景稳定性、重试成本。

| 排名 | 模型/服务 | 建议定位 | 采购动作 |
|------|-----------|----------|----------|
| 1 | Runway Gen-4 Turbo | 日更 B-roll 第一外部候选。官方 API 按 credits/sec 计费，Gen-4 Turbo 单秒成本清晰，适合批量横评。 | 先完成接口适配和Mock/占位素材流程；系统稳定后再小额购买，跑攸县样例横评。 |
| 2 | Google Veo 3.1 Lite/Fast | 重点镜头候选。官方 Vertex AI 定价显示 Lite/Fast 分层，Lite/Fast 可在质量和成本间切换。 | 只用于重点镜头、宣传片或 Runway 失败镜头。 |
| 3 | Kling API | 中文提示词和短视频生态适配可能较好，API 文档公开但价格和地区限制需控制台实测。 | 与 Runway 同提示词横评，适合中文场景候选。 |
| 4 | Luma Ray / Pika | 创意镜头、物理运动和风格化候选；适合特定镜头补位。 | 暂不年付，按镜头需求小额测试。 |
| 5 | MiniMax Hailuo-2.3 / Hailuo-2.3-Fast | 已购兜底/基线对照。因你反馈 MiniMax 效果弱，不再作为冷启动主线。 | 只在外部服务不可用、成本异常或样例盲测胜出时使用。 |

来源：[Runway API Pricing](https://docs.dev.runwayml.com/guides/pricing/)、[Google Vertex AI Pricing - Veo](https://cloud.google.com/vertex-ai/generative-ai/pricing)、[Kling API Docs](https://klingapi.com/docs)、[Luma API Pricing](https://lumalabs.ai/api/pricing)、[MiniMax API Release Notes](https://platform.minimax.io/docs/release-notes/apis)

### 2.5 数字人：先验证 HeyGen，再准备 API 备选

数字人是本项目最大新增成本项。核心不是模型参数，而是：口型同步、普通话/方言音频适配、竖屏输出、API 权限、并发和每分钟成本。

| 排名 | 服务 | 适合场景 | 采购/测试建议 |
|------|------|----------|---------------|
| 1 | HeyGen Avatar IV/V | 质量和成熟度优先的 30-90 秒口播。官方 API 文档有按输出时长的计费。 | 先完成虚拟本地人设、接口预留和配置页；系统稳定后再购买/确认 API，用低成本档验证。 |
| 2 | Tavus | API 产品化强，适合需要实时交互、Replica、或后续做直播/客服式数字人。 | 若 HeyGen 成本高或 API 受限，买 Starter 横评。 |
| 3 | D-ID | 单图说话、低延迟、接入简单，适合快速低成本兜底。 | 做“应急数字人/低成本口播”测试。 |
| 4 | AKOOL | API 价格项覆盖 Talking Avatar、Streaming Avatar、LipSync，适合营销批量化。 | 如果需要多头像营销素材，再购买小额 credits。 |
| 5 | Synthesia | 培训、企业讲解、多语言课程强；Creator 才含 API。 | 不作为攸县短视频日更主线。 |
| 6 | 腾讯智影/剪映数字人 | 国内平台生态、中文模板、人工半自动方便。 | 用作低成本人工兜底，不强求 API 自动化。 |

来源：[HeyGen API Pricing](https://developers.heygen.com/docs/pricing)、[Tavus Pricing](https://www.tavus.io/pricing)、[D-ID API](https://www.d-id.com/api/)、[AKOOL API Pricing](https://akool.com/api-pricing)、[Synthesia Pricing](https://www.synthesia.io/pricing)

### 2.6 New API 中转站的正确定位

New API 类型网关的价值在于把不同供应商适配成 OpenAI 兼容接口，降低调用侧复杂度。它不应被等同为“模型效果差”，但也不能完全忽略通道差异。

技术策略：
- `channel=official`：官方订阅，优先用于账号、私密、商业数据和稳定生产。
- `channel=new_api_relay`：中转站兼容通道，可用于主链路，但必须记录通道、响应、成本、失败率和能力差异。
- `channel=local_tool`：FFmpeg、规则库、数据库、检索索引等本地工具。

管控重点：
- 连通性：每天 smoke test。
- 能力差异：是否支持 Responses、Chat Completions、图片编辑、文件上传、函数调用、JSON schema。
- 成本差异：按中转站账单回填真实成本，不能只按官方价格估算。
- 数据策略：账号凭证、Cookie、API Key 不进任何生成模型；未公开商业数据按最小必要原则传递。

来源：[New API Feature Guide](https://www.newapi.ai/en/docs/guide/feature-guide)、[New API API Reference](https://docs.newapi.ai/en/docs/api)

---

## 三、专业场景模型搭配

### 3.1 选题检索与创意发散

| 阶段 | 主模型/工具 | 备选 | 说明 |
|------|-------------|------|------|
| 信息检索 | 搜索 API + Playwright + 结构化来源表 | MiMo Omni 做网页/图片理解 | 明确事实尽量检索；历史/风俗类允许民间说法和爆款演绎，但必须做风险分级。 |
| 批量创意 | DeepSeek V4 Flash | MiMo V2.5、GLM-5.1 轻量调用 | 一次生成 30-50 个候选，低成本可重试；MiniMax M2.7 只作为基线对照。 |
| 深度筛选 | GLM-5.1 | GPT-5.5、DeepSeek V4 Pro | 按本地性、冲突点、可拍性、风险、素材难度打分。 |
| 反方评审 | GPT-5.5 / Claude Opus Relay | GLM-5.1 | 检查是否俗套、是否过度臆测、是否有平台风险。 |

### 3.2 方言脚本创作

| 阶段 | 主模型/工具 | 备选 | 说明 |
|------|-------------|------|------|
| 初稿 | DeepSeek V4 Flash | MiMo V2.5 | 生成多个结构版本，不追求一次成稿。 |
| 方言化 | 方言词典 RAG + GLM-5.1 | DeepSeek V4 Pro、MiMo Pro | 方言不能靠模型猜，必须有语料库约束。 |
| 口播润色 | MiMo V2.5 Pro | GLM-5.1、GPT-5.5 | 强调短句、停顿、口语节奏；MiniMax M2.7 仅作为兜底/基线。 |
| 终审 | GLM-5.1 | GPT-5.5、DeepSeek V4 Pro | 检查事实、节奏、钩子、敏感和平台适配。 |

### 3.3 分镜与视觉设计

| 阶段 | 主模型/工具 | 备选 | 说明 |
|------|-------------|------|------|
| 分镜 JSON | GLM-5.1 | GPT-5.5、DeepSeek V4 Pro | 严格输出镜头编号、画面、台词、素材、时长和生成方式。 |
| 封面图 | GPT-image-2 | Firefly/Imagen/Seedream/FLUX 横评；MiniMax image-01 最后兜底 | 主线直接使用 GPT-image-2，MiniMax 不做直接第二选择。 |
| 分镜参考图 | GPT-image-2 | Firefly/Imagen/Seedream/FLUX 横评；MiniMax image-01 最后兜底 | 用于审核和 B-roll 提示词，不直接等同最终画面。 |
| 图片质检 | MiMo Omni | GPT-5.5 Vision Relay、GLM-5.1 | 检查文字空间、画面噪声、地域错误、人物手部/食品异常；MiniMax M2.7 只作基线。 |

### 3.4 视频 B-roll

| 场景 | 主模型 | 备选 | 说明 |
|------|--------|------|------|
| 批量空镜草稿 | Runway Gen-4 Turbo | Kling、Luma Ray | 按单秒成本、可用率和重试成本跑 30 条样例。 |
| 重点镜头 | Veo 3.1 Lite/Fast | Runway Gen-4 Turbo | 景点、美食特写、人物动作需要更高可用率。 |
| 高真实运动 | Veo 3.1 Lite/Fast | Runway Gen-4 Turbo | 成本高，只给爆款候选或宣传片。 |
| 风格化镜头 | Luma Ray / Pika | Hailuo 标准版最后兜底 | 暂不年付，按样例需求临时评估。 |

### 3.5 方言配音、角色声音与音乐

| 阶段 | 主模型/工具 | 备选 | 说明 |
|------|-------------|------|------|
| 主配音 | MiMo VoiceClone | ElevenLabs；MiniMax Speech 2.8 最后兜底 | 按音色相似度、方言咬字、稳定性盲评。 |
| 快速草稿音频 | MiMo TTS | OpenAI TTS；MiniMax Speech 2.8 最后兜底 | 用于内部审核，不一定发布。 |
| 角色声线 | MiMo VoiceDesign | ElevenLabs / Cartesia；MiniMax Voice Design 最后兜底 | 生成非本人角色声线。 |
| 外部高质量横评 | ElevenLabs Multilingual / Cartesia Sonic | OpenAI TTS | 小米方言效果低于 3.5/5 时优先购买小额测试。 |
| BGM | 剪映商用可用素材 / 免版权库 / Artlist / Epidemic Sound | Suno 或 ElevenLabs Music；MiniMax Music 2.6 最后实验 | 必须保留来源、提示词、授权和商用范围记录。 |

### 3.6 数字人口播

| 阶段 | 主服务 | 备选 | 说明 |
|------|--------|------|------|
| MVP 主线 | HeyGen | Tavus | 先验证 9:16、口型、API、时长成本。 |
| 低成本兜底 | D-ID | AKOOL Talking Avatar | 单图说话或简单口播，质量不如 HeyGen 时仅用于非重点内容。 |
| 平台生态兜底 | 剪映数字人 / 腾讯智影 | 人工模板 | API 不稳定时保留半自动流程。 |

### 3.7 数据分析与运营复盘

| 阶段 | 主模型/工具 | 备选 | 说明 |
|------|-------------|------|------|
| 日报 | DeepSeek V4 Flash | MiMo V2.5 | 汇总播放、点赞、完播、评论关键词。 |
| 周报 | GLM-5.1 | GPT-5.5、DeepSeek V4 Pro | 选题归因、平台差异、下周策略。 |
| 竞品趋势 | 搜索 API + 蝉妈妈/飞瓜可选 | Playwright | 冷启动先用免费/低成本数据，连续 4 周后再买付费版。 |

---

## 四、Agent 搭配优化

对用户界面仍展示 3 个 Agent，降低使用复杂度；内部实现拆成 5 个执行 Agent + 2 个 Gate。

| 类型 | 名称 | 职责 | 默认模型/工具 |
|------|------|------|---------------|
| 执行 | Research Agent | 攸县资料、热点、竞品、素材来源检索 | 搜索 API、Playwright、DeepSeek Flash、MiMo |
| 执行 | Script Agent | 选题、脚本、方言化、字幕 | DeepSeek Flash、MiMo、GLM-5.1、方言 RAG；MiniMax M2.7 仅基线 |
| 执行 | Storyboard Agent | 分镜、封面、B-roll 提示词、镜头清单 | GLM-5.1、GPT-image-2、Runway/Veo/Kling 提示词；MiniMax image-01 仅兜底 |
| 执行 | Production Agent | TTS、数字人、B-roll、音乐、FFmpeg 合成 | MiMo、ElevenLabs/Cartesia 候选、Runway/Veo/Kling/Luma、HeyGen；MiniMax/Hailuo 仅兜底 |
| 执行 | Ops Agent | 发布排期、数据采集、周报、复盘 | DeepSeek Flash、GLM-5.1、搜索/数据工具 |
| Gate | Quality Gate | 钩子、节奏、事实、画面、音频质检 | GLM-5.1、MiMo Omni、GPT-5.5 Vision；MiniMax M2.7 仅基线 |
| Gate | Compliance Gate | AI 标识、版权、声音授权、平台规则 | 本地规则库 + GLM-5.1 |

编排边界：
- n8n：定时触发、等待人工审核、通知、Webhook、长耗时任务串联。
- LangGraph：Agent 状态机、模型路由、失败重试、人工断点、回滚。
- FastAPI：任务 API、状态查询、回调入口。
- MCP/tool adapter：封装搜索、模型、素材库、FFmpeg、发布和数据采集工具。

---

## 五、工具搭配优化

| 环节 | 推荐工具 | 关键要求 |
|------|----------|----------|
| 编排 | n8n + LangGraph | n8n 处理外部流程，LangGraph 管 Agent 状态和重试。 |
| 服务层 | FastAPI + SQLite WAL | MVP 够用；产量上升后迁 PostgreSQL。 |
| 检索 | 搜索 API + Playwright | 明确事实、地名、景区、美食信息尽量有来源；历史/风俗内容的来源作为质量护栏，不作为爆款共创硬阻塞。 |
| 知识库 | SQLite-vec 或 Qdrant | 方言词典、脚本案例、素材标签进入可检索库。 |
| 图像 | GPT-image-2 + Firefly/Imagen/Seedream/FLUX 横评 + MiniMax image-01 最后兜底 | 主线高质量，MiniMax 不做直接第二选择。 |
| 语音 | MiMo TTS 系列 + ElevenLabs/Cartesia/OpenAI TTS 横评 + MiniMax Speech 2.8 最后兜底 | 必须做盲测和声音授权记录。 |
| 视频 | Runway/Veo/Kling/Luma/Pika + Hailuo 最后兜底 | 先做适配器和占位素材流程；系统稳定后按效果成本比小额横评，不再因已购而默认 Hailuo 主线。 |
| 数字人 | 虚拟本地人设 + HeyGen/Tavus/D-ID/AKOOL 候选 | 先做人设和接口预留；采购后记录每分钟成本、口型评分和失败率。 |
| 合成 | FFmpeg + 剪映模板 | FFmpeg 批量，剪映人工精修。 |
| 观测 | model_call_logs + eval_models.py | 每次调用记录成本、延迟、通道、质量分。 |

---

## 六、模型注册中心字段建议

```python
@dataclass
class ModelOption:
    id: str
    name: str
    provider: str
    channel: str                  # official / new_api_relay / official_or_relay / local_tool
    modalities: list[str]         # text / image / video / audio / avatar / tool
    api_base: str
    model_name: str
    api_key_env: str
    quality_tier: str = "normal"  # draft / normal / high / flagship
    cost_tier: str = "normal"     # low / normal / high
    latency_tier: str = "normal"  # fast / normal / slow
    data_policy: str = "standard" # public_only / standard / sensitive_allowed / local_only
    api_compatibility: str = ""   # openai_chat / openai_responses / native / async_task
    supports_json: bool = False
    supports_tools: bool = False
    supports_streaming: bool = True
    supports_image_edit: bool = False
    supports_reference_image: bool = False
    supports_9_16: bool = False
    fallback_ids: list[str] = field(default_factory=list)
    notes: str = ""
```

路由伪代码：

```python
class ModelRouter:
    DEEP_REASONING = ["glm_5_1_relay", "gpt_5_5_relay", "deepseek_v4_pro"]
    IMAGE_PRIMARY = ["gpt_image_2_relay", "firefly", "imagen", "seedream", "flux", "minimax_image_01"]
    VOICE_PRIMARY = ["mimo_voiceclone", "mimo_voicedesign", "mimo_tts", "elevenlabs", "cartesia", "openai_tts", "minimax_speech_2_8"]
    VIDEO_PRIMARY = ["runway_gen4_turbo", "veo_3_1_lite", "veo_3_1_fast", "kling", "luma_ray", "pika", "hailuo_2_3", "hailuo_2_3_fast"]
    AVATAR_PRIMARY = ["heygen_avatar", "tavus_replica", "d_id_talking_avatar", "akool_talking_avatar"]

    def select(self, task_type: str, quality: str = "normal", data_policy: str = "standard"):
        if task_type in {"strategy", "architecture_review", "script_diagnosis", "weekly_strategy"}:
            return self.first_available(self.DEEP_REASONING, data_policy)
        if task_type in {"cover", "storyboard_reference", "scene_image"}:
            return self.first_available(self.IMAGE_PRIMARY, data_policy)
        if task_type in {"voice_clone", "voiceover", "role_voice"}:
            return self.first_available(self.VOICE_PRIMARY, data_policy)
        if task_type in {"broll", "image_to_video", "text_to_video"}:
            return self.first_available(self.VIDEO_PRIMARY, data_policy)
        if task_type in {"digital_human", "avatar_video", "lip_sync"}:
            return self.first_available(self.AVATAR_PRIMARY, data_policy)
        if task_type in {"topic_batch", "title_batch", "tags", "daily_report"}:
            return self.by_id("deepseek_v4_flash")
        return self.by_id("mimo_v2_5")
```

---

## 七、实测评估方案

上线前用 70 个项目样例横评，不靠供应商宣传决定主力模型。

| 类别 | 样例数 | 候选模型/服务 | 评分维度 |
|------|--------|---------------|----------|
| 选题创意 | 10 | DeepSeek Flash、MiMo、GLM-5.1、MiniMax M2.7 基线 | 本地性、冲突点、可拍性、风险。 |
| 深度推理 | 8 | GLM-5.1、GPT-5.5、DeepSeek V4 Pro | 推理链、反例、可执行性、稳定 JSON。 |
| 方言脚本 | 12 | GLM-5.1、DeepSeek Pro、MiMo Pro、MiniMax M2.7 基线 | 方言自然度、节奏、钩子、事实来源。 |
| 图像/封面 | 10 | GPT-image-2、Firefly/Imagen/Seedream/FLUX、MiniMax image-01 兜底 | 点击欲望、真实感、文字空间、风格一致性。 |
| 语音 | 10 | MiMo VoiceClone/TTS、ElevenLabs、Cartesia、OpenAI TTS、MiniMax Speech 基线 | 音色、方言咬字、情绪、稳定性、成本。 |
| 视频 B-roll | 10 | Runway、Veo、Kling、Luma/Pika、Hailuo 基线 | 可用率、运动稳定、9:16、重试成本、生成耗时。 |
| 数字人 | 6 | HeyGen、Tavus、D-ID、AKOOL、腾讯智影/剪映 | 口型、表情、竖屏、API、每分钟成本。 |
| 数据分析 | 4 | GLM-5.1、GPT-5.5、DeepSeek Pro | 归因质量、反事实、行动建议。 |

通过门槛：
- 单项低于 3/5：不得进入自动发布链路。
- 主链路模型平均分需大于 3.8/5。
- 同分时优先选择成本更低、失败率更低、API 更稳定的模型。
- 每月复测一次，因为官方模型和中转站路由都可能变化。

---

## 八、追加采购建议

### 8.1 搭建期先确认但暂不购买

| 项目 | 建议 | 理由 |
|------|------|------|
| HeyGen API/套餐 | 暂不购买；先确认能力、API权限、Avatar类型、9:16输出、并发和计费方式，完成系统配置预留。 | 数字人口播是核心缺口，但采购放到系统稳定后。 |
| 对象存储 | 可先本地文件系统起步；接入HeyGen/Runway前再从阿里云OSS、腾讯COS或Cloudflare R2中选一个。 | 数字人、视频模型、回调和成片分发需要稳定URL，但非第一天阻塞项。 |
| 搜索 API | 先接入可用搜索通道；稳定后再购买更可靠的搜索API。 | 事实检索和竞品监控需要来源，但MVP可先低成本起步。 |

### 8.2 进入小额横评池

| 项目 | 购买条件 | 建议 |
|------|----------|------|
| Runway API | 系统搭建期暂不购买；接口和Mock流程完成后进入第一横评池。 | 系统稳定后再小额度购买 Gen-4 Turbo，和 Hailuo 基线同题比较。 |
| Google Veo | 需要高真实运动、音画同步或宣传片级镜头。 | 买最小可用额度，只做重点镜头。 |
| Kling API | 需要中文短视频生态适配，或 Runway/Veo 成本过高。 | 与 Runway/Veo/Hailuo 基线同提示词横评。 |
| ElevenLabs / Cartesia | 小米方言语音低于 3.5/5，或需要更强情绪/角色声线。 | 先少量测试，不直接年付；MiniMax Speech 只做最后兜底。 |
| Tavus / D-ID / AKOOL | HeyGen 成本、API、口型或审核限制不满足MVP验证。 | 采购HeyGen验证后再选择1-2个替代横评，不在搭建期购买。 |

### 8.3 暂不建议购买

| 项目 | 原因 |
|------|------|
| 额外通用大模型官方订阅 | 你当前问题不是大模型数量不足，而是路由、评估和媒体链路稳定性不足。 |
| 云 GPU / 本地训练方案 | 你明确没有 GPU 资源，且 API 模型已覆盖 MVP。 |
| 复杂 RAG 平台 | MVP 阶段 SQLite-vec/Qdrant + 结构化方言词典足够。 |
| 全自动发布 SaaS | 平台权限和风控差异大，应先官方 API + Playwright + 人工兜底。 |

---

## 九、最终推荐搭配

| 场景 | 第一选择 | 第二选择 | 第三选择 |
|------|----------|----------|----------|
| 批量选题 | DeepSeek V4 Flash | MiMo V2.5 | GLM-5.1 轻量调用 / MiniMax M2.7 基线 |
| 深度策略/推理 | GLM-5.1 | GPT-5.5 | DeepSeek V4 Pro |
| 脚本初稿 | DeepSeek V4 Flash | MiMo V2.5 | GLM-5.1 轻量调用 / MiniMax M2.7 基线 |
| 脚本定稿 | GLM-5.1 + 方言 RAG | DeepSeek V4 Pro | MiMo V2.5 Pro |
| 口语润色 | MiMo V2.5 Pro | GLM-5.1 | GPT-5.5 / MiniMax M2.7 基线 |
| 分镜 JSON | GLM-5.1 | GPT-5.5 | DeepSeek V4 Pro |
| 封面/图片 | GPT-image-2 | Firefly/Imagen/Seedream/FLUX 横评 | MiniMax image-01 最后兜底 |
| 主配音 | MiMo VoiceClone | MiMo TTS / ElevenLabs小额横评 | MiniMax Speech 2.8 最后兜底 |
| 角色声线 | MiMo VoiceDesign | ElevenLabs/Cartesia 横评 | MiniMax Voice Design 最后兜底 |
| 数字人 | HeyGen | Tavus | D-ID/AKOOL |
| B-roll | Runway Gen-4 Turbo | Veo 3.1 Lite/Fast / Kling | Hailuo-2.3/Fast 基线兜底 |
| 高质量视频镜头 | Runway Gen-4 Turbo | Veo 3.1 Fast/Lite | Kling |
| BGM | 剪映商用素材/免版权库 | Artlist/Epidemic Sound | Suno/ElevenLabs Music 横评；MiniMax Music 2.6 最后实验 |
| 合成 | FFmpeg | 剪映模板 | 人工精修 |
| 发布 | 平台 API + Playwright | 半自动人工 | 全人工兜底 |
| 日报 | DeepSeek V4 Flash | MiMo V2.5 | GLM-5.1 轻量调用 / MiniMax M2.7 基线 |
| 周报/复盘 | GLM-5.1 | GPT-5.5 | DeepSeek V4 Pro |

---

## 十、自主评审结论

| 角色 | 评审结论 | 已处理 |
|------|----------|--------|
| 产品 | 原方案过度强调“已购模型优先”，没有充分体现你对 `gpt-image-2`、小米语音和深度推理顺序的真实偏好。 | 已改为场景化路由和明确优先级。 |
| 研发 | 旧字段把 New API 中转模型按通道降级，且缺少图像/视频/数字人能力字段。 | 已改为 `channel`、`data_policy`、`api_compatibility`、`quality_tier` 等字段。 |
| 测试 | 旧横评只覆盖文本和少量媒体，不足以决定视频、语音、数字人采购。 | 已扩展为 70 样例、多媒体横评。 |
| 运营 | 旧采购建议过于保守，未给出何时买 Runway/Veo/Tavus/D-ID 等触发条件。 | 已给出小额横评池和触发门槛。 |
| 合规 | 声音克隆、AI 图像、数字人、版权音乐都需要授权和 AI 标识。 | 已要求保留来源、授权、提示词、合成记录。 |

### 10.1 二次复评迭代（MiniMax 降级后）

| 角色 | 复评结论 | 处理结果 |
|------|----------|----------|
| 产品 | 新约束“MiniMax 效果不高，不优先使用”已影响所有主链路，不能只在单点备注。 | 已将 MiniMax 全系列降为基线/最后兜底，并同步到图像、语音、视频、音乐、Agent 和评测表。 |
| 研发 | 技术规格若仍把 Hailuo 或 MiniMax 放在 `active_id` / `PRIMARY` 数组前位，会导致实现偏离策略。 | 已把视频默认路由改为 Runway → Veo → Kling → Luma/Pika → Hailuo，语音改为 MiMo → 外部语音 → MiniMax。 |
| 测试 | 不能用“已购”代替质量判断，必须同题横评。 | 已要求 70 样例集内保留 MiniMax/Hailuo 作为基线，和外部模型同提示词、同评分维度比较。 |
| 运营 | 采购动作需要从“立即购买”改为“先搭建适配器和Mock流程，系统稳定后小额横评”。 | 已将 Runway/HeyGen 改为接口预留 + 稳定后小额验证，Veo/Kling/Luma/Pika 作为条件触发候选。 |
| 合规 | BGM、声音克隆、数字人、AI 图像都涉及授权和标识，MiniMax Music 不应因已购而默认可商用。 | 已把 BGM 主线改为剪映商用素材/免版权库/Artlist/Epidemic，AI 音乐只做有授权记录的实验。 |

最终判断：当前三份方案已对齐“效果和成本最均衡优先、MiniMax 仅兜底/基线、无本地训练/GPU路线”的新约束。所有主链路仍需用真实样例验证，不应只凭供应商宣传或单次主观感受定型。




