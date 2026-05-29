# MiMo TTS / CosyVoice 方言克隆调研报告

> 调研日期：2026-05-28
> 目标：为攸县方言短视频配音系统寻找可行的方言语音克隆方案

---

## 1. 执行摘要

本调研覆盖了以下方言语音合成/克隆方案：

| 方案 | 方言支持度 | 攸县方言可行性 | 推荐度 |
|------|-----------|---------------|--------|
| **CosyVoice 3.0 (阿里FunAudioLLM)** | 18+中文方言+跨语言零样本克隆 | **高** - 零样本克隆，一条参考音频即可 | 强烈推荐 |
| MiMo TTS (小米端侧大模型) | 存在方言克隆API，细节待确认 | 中 - 公开文档有限 | 观望 |
| GPT-SoVITS | 需训练，方言需自行准备数据 | 中 - 需收集攸县方言数据训练 | 备选 |
| ElevenLabs | 支持中文，不支持中文方言 | 低 - 不直接支持方言 | 不推荐 |
| 科大讯飞 TTS | 支持主要方言(粤/川/闽等)，无湘语 | 低 - 不支持湘语 | 不推荐 |
| 百度/腾讯云 TTS | 仅支持普通话��有限方言 | 低 - 不支持攸县话 | 不推荐 |

**核心结论**: **阿里 CosyVoice 3.0 是目前最适合的方案**，其零样本语音克隆能力理论上可以"用一条攸县话参考音频，克隆出攸县方言语音"。CosyVoice 2.0 和 3.0 均开源且免费。

---

## 2. CosyVoice 详细分析（推荐方案）

### 2.1 项目概况

- **开发方**: 阿里云通义实验室 (Tongyi SpeechTeam)
- **GitHub**: https://github.com/FunAudioLLM/CosyVoice
- **许可证**: Apache 2.0 (开源)
- **最新版本**: Fun-CosyVoice 3.0 (v3.0, 2025年12月发布)
- **模型大小**: 0.5B 参数

### 2.2 版本对比

| 特性 | CosyVoice 1.0 | CosyVoice 2.0 | CosyVoice 3.0 (最新) |
|------|--------------|--------------|---------------------|
| 发布时间 | 2024.07 | 2024.12 | 2025.12 |
| 语言覆盖 | 中/英/日/粤 | + 韩语 | 9种语言 + 18+方言口音 |
| 方言支持 | 粤语 | 粤语 | 广东/闽南/四川/东北/陕西(山/陕)/上海/天津/山东/宁夏/甘肃/湖南/湖北/河南/贵州/江西/云南等 18+ |
| 零样本克隆 | 支持 | 支持 | 支持 |
| 流式推理 | 有限 | 支持(kv cache) | 双向流式(150ms延迟) |
| 发音修复 | - | - | 拼音/CMU音素注入 |
| Instruct控制 | 基础 | 方言+情感 | 方言+情感+语速+音量 |

### 2.3 方言支持（关键发现）

在 CosyVoice 3.0 的代码 (`cosyvoice/utils/common.py`) 中，明确列出了通过 instruct 模式支持的方言指令：

```
可用方言指令（直接调用）:
1. 广东话 (Cantonese / yue)
2. 东北话
3. 甘肃话
4. 贵州话
5. 河南话
6. 湖北话
7. **湖南话** ← 攸县话所属的湘语大类别
8. 江西话
9. 闽南话
10. 宁夏话
11. 山西话
12. 陕西话
13. 山东话
14. 上海话
15. 四川话
16. 天津话
17. 云南话
```

此外，README 中明确说明 CosyVoice 3.0 支持 "18+ Chinese dialects/accents" 并涵盖 "Guangdong, Minnan, Sichuan, Dongbei, Shan3xi, Shan1xi, Shanghai, Tianjin, Shandong, Ningxia, Gansu, etc."。

### 2.4 攸县方言可行性分析

攸县方言属于 **湘语（湖南话）** 的娄邵片。CosyVoice 3.0 的方言能力分两层：

| 方法 | 原理 | 攸县方言效果预期 |
|------|------|-----------------|
| **零样本方言克隆** (zero-shot) | 提供一段攸县话参考音频，模型直接克隆其音色+口音 | **最高** - 最贴近真实攸县话 |
| **方言指令** (instruct) | 用"请用湖南话表达"指令驱动方言口音 | 中等 - 是广义湖南话，非特指攸县话 |
| **跨语言克隆** (cross-lingual) | 用中文参考音频驱动其他语言内容 | 可用于混合场景 |

**零样本克隆流程**:
```
1. 准备一条攸县话参考音频 (3-30秒，清晰无噪音)
2. 提供文本：希望克隆的参考音频的文字内容
3. 提供待合成文本：要生成的攸县话内容
4. 推理：cosyvoice.inference_zero_shot()
5. 输出：攸县话语音
```

### 2.5 API 和部署方式

| 方式 | 说明 |
|------|------|
| 本地 Python 推理 | `python example.py` - 直接调用，无需网络 |
| WebUI | `python webui.py --port 50000` - 图形界面 |
| FastAPI 服务 | 提供 HTTP API (`runtime/python/fastapi/server.py`) |
| gRPC 服务 | 高性能部署 (`runtime/python/grpc/server.py`) |
| vLLM 推理 | 支持 vllm 0.11.x+ 高性能推理 |
| Docker 部署 | 一键 docker build |
| ModelScope | 在线模型下载和推理 |

### 2.6 测试/体验方式

| 平台 | 地址 |
|------|------|
| CosyVoice 3.0 Demo | https://funaudiollm.github.io/cosyvoice3/ |
| CosyVoice 2.0 Demo | https://funaudiollm.github.io/cosyvoice2/ |
| ModelScope Gradio | 见 GitHub README 链接 |
| HuggingFace 模型 | https://huggingface.co/FunAudioLLM |

### 2.7 硬件要求

- CosyVoice 2.0/3.0 均为 0.5B 参数模型
- GPU 推荐: 至少 4GB VRAM (推理), 训练��要更大
- CPU 推理: 可用但速度慢
- 支持 INT8 量化

---

## 3. MiMo TTS 分析

### 3.1 已知信息

- **开发者**: 小米 (Xiaomi MiMo 端侧大模型团队)
- **GitHub 组织**: https://github.com/Xiaomi-MiMo
- **官方文档**: https://platform.xiaomimimo.com/docs (存在但无法直接访问)
- **社区讨论**: 百度贴吧中有相关讨论 (tieba.baidu.com/p/9560760990)

### 3.2 已知能力

据百度贴吧讨论，MiMo TTS 包含:
- 语音克隆 (Voice Clone)
- 方言克隆 (Dialect Clone)
- TTS v2.5 API

### 3.3 问题与风险

- **无公开API文档**: 虽然有 GitHub 组织 (Xiaomi-MiMo) 和疑似 API 文档仓库 (mimo-tts-api-docs)，但仓库无法访问（可能为内部/私有）
- **平台不可访问**: platform.xiaomimimo.com 无法通过 WebFetch 访问
- **无定价信息**: 未找到公开的定价和接入方式
- **合规性不明**: 不确定是否需要企业合作或资质审核

**结论**: MiMo TTS 可能具备方言克隆能力，但现阶段信息不足，无法作为可靠方案。建议持续关注。

---

## 4. 其他方案对比

### 4.1 GPT-SoVITS

| 维度 | 评价 |
|------|------|
| **方言能力** | 支持任何语言/方言，但需要**收集数据自行训练** |
| **适合场景** | 有固定说话人+大量语料的场景 |
| **数据需求** | 需要 1-30 分钟纯语音+对应文本 |
| **训练成本** | 需要 GPU 训练 (1-3 小时) |
| **与 CosyVoice 对比** | CosyVoice 零样本即用，GPT-SoVITS 需训练 |

### 4.2 ElevenLabs

| 维度 | 评价 |
|------|------|
| **中文支持** | 支持普通话 (包含在 multilingual v2 模型中) |
| **方言支持** | 不直接支持中文方言 |
| **语音克隆** | 支持，但克隆中文方言的效果未经广泛验证 |
| **定价** | 付费 API (约 $5/月起) |
| **适用性** | 不适合攸县方言场景 |

### 4.3 科大讯飞 TTS

| 维度 | 评价 |
|------|------|
| **方言支持** | 粤语、四川话、闽南语等主流方言 |
| **湘语/湖南话** | 未找到明确支持信息 |
| **定价** | 商业 API，按调用量付费 |
| **适用性** | 不支持攸县方言 |

---

## 5. 推荐方案：CosyVoice 详细技术方案

### 5.1 部署架构

```
[短视频系统] -> HTTP API -> [CosyVoice FastAPI Server] -> GPU推理 -> 音频输出
                             或
[短视频系统] -> Python SDK -> [CosyVoice AutoModel] -> GPU/CPU推理 -> 音频输出
```

### 5.2 零样本方言克隆流程详解

```
Step 1: 准备参考音频
  - 录制约 10 秒攸县话语音
  - 内容不限（如"大家好，我是攸县人"）
  - 要求: 清晰、无噪音、单说话人

Step 2: 提取说话人特征 (SPK)
  - 使用参考音频和对应文本
  - 保存为 SPK 嵌入供后续复用

Step 3: 方言推理
  - 提供待合成文本（攸县话/普通话混合均可）
  - 提供参考 SPK
  - 输出攸县口音语音
  
Step 4: (可选) 方言微调
  - 若有更多攸县方言数据，可 SFT 微调
  - 提升方言口音准确度
```

### 5.3 推荐实现路径

| 阶段 | 工作 | 预期耗时 |
|------|------|---------|
| **Phase 1** | 部署 CosyVoice 2.0 (更成熟) 并测试方言克隆效果 | 1-2天 |
| **Phase 2** | 录制高质量攸县方言参考音频 | 1天 |
| **Phase 3** | 验证零样本克隆效果，评估是否满足短视频配音质量要求 | 1-2天 |
| **Phase 4** | (可选) 升级到 CosyVoice 3.0 获取更好的方言支持 | 1天 |
| **Phase 5** | 集成到短视频系统的 API 服务流程 | 2-3天 |

### 5.4 关键参数建议

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 参考音频长度 | 10-30秒 | 太短克隆不稳定，太长收益递减 |
| 参考音频采样率 | 22050Hz (模型原生) | 保持与模型一致 |
| 参考音频格式 | WAV/MP3 | 推荐 WAV |
| 推理模式 | zero_shot | 零样本克隆 |
| 流式推理 | 可选 | 开启后延迟约150ms |

---

## 6. 局限性说明

### 6.1 CosyVoice 局限性

1. **零样本 ≠ 完美克隆**: 第一次克隆可能有音色或韵律偏差，需要通过 prompt 工程优化
2. **"湖南话" ≠ "攸县话"**: Instruct 模式下的"湖南话"是广义湖南口音，不一定精确对应攸县土话。建议优先使用零样本克隆
3. **硬件需求**: 0.5B 模型需要 GPU（建议 4GB+ VRAM），纯 CPU 推理速度较慢
4. **长文本处理**: 极长文本可能需要分片或使用流式模式
5. **日本语特殊要求**: 日语输入须转为片假名——这一般不涉及攸县方言场景

### 6.2 攸县方言自身挑战

1. **濒危性**: 攸县话作为湘语娄邵片方言，使用人口约 80 万，不属于主流方言
2. **语料稀缺**: 较难找到公开的高质量攸县话数据集
3. **音系差异**: 攸县话与普通话差异大，包含更多声母/韵母特殊发音
4. **参考音频要求**: 需要找到能流利说地道攸县话的发音人录制参考音频

### 6.3 其他方案局限性

- MiMo TTS: 文档不可访问，无法评估
- GPT-SoVITS: 方言数据需求高，攸县话语料极稀缺
- ElevenLabs/讯飞: 不支持湘语方言

---

## 7. 最终建议

### 推荐方案 (排序)

| 优先级 | 方案 | 理由 |
|--------|------|------|
| **1st** | **CosyVoice 3.0 零样本克隆** | 开源免费、18+方言支持、零样本即用，一条攸县话参考音频即可 |
| 2nd | CosyVoice 2.0 + 零样本 | 更成熟稳定，作为首选备选 |
| 3rd | GPT-SoVITS + 回源训练 | 如果零样本效果不够，可用少量数据进行微调 |
| 4th | 持续关注 MiMo TTS | 若能获取 API 文档，可能是一个好的云端方案 |

### 立即行动项

1. 体验 CosyVoice 3.0 Demo (https://funaudiollm.github.io/cosyvoice3/) 测试方言效果
2. 准备一条高质量的攸县话参考音频（找本地人录制 10-30 秒）
3. 部署 CosyVoice 2.0 本地服务进行方言克隆 POC
4. 验证 POC 结果是否满足短视频配音的质量要求

---

## 8. 参考资料

- CosyVoice GitHub: https://github.com/FunAudioLLM/CosyVoice
- CosyVoice 3.0 Demo: https://funaudiollm.github.io/cosyvoice3/
- CosyVoice 2.0 Demo: https://funaudiollm.github.io/cosyvoice2/
- CosyVoice 3.0 Paper: https://arxiv.org/pdf/2505.17589
- CosyVoice 2.0 Paper: https://arxiv.org/pdf/2412.10117
- ModelScope 模型下载: https://www.modelscope.cn/models/FunAudioLLM
- HuggingFace 模型: https://huggingface.co/FunAudioLLM
- Alibaba Cloud CosyVoice 2: https://www.alibabacloud.com/cosyvoice-2
- MiMo GitHub 组织: https://github.com/Xiaomi-MiMo
- MiMo TTS 平台: https://platform.xiaomimimo.com/docs
- 社区讨论: https://tieba.baidu.com/p/9560760990
