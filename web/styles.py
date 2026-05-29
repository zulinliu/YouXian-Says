"""全局样式注入模块 — 浅色简约风格设计系统 + Remix Icon + 共享 UI 组件"""

import html

import streamlit as st

# ── 设计 Token ──────────────────────────────────────────────

COLORS = {
    "primary": "#E07A5F",
    "primary_dark": "#C4613F",
    "primary_light": "#FEF2EE",
    "accent": "#3D8B7A",
    "accent_dark": "#2D6B5E",
    "accent_light": "#EFF8F5",
    "bg": "#F8F6F3",
    "bg_deep": "#F0EDE8",
    "card": "#FFFFFF",
    "fg": "#292524",
    "fg_light": "#44403C",
    "muted": "#78716C",
    "muted_light": "#A8A29E",
    "border": "#E7E5E4",
    "border_hover": "#D6D3D1",
    "success": "#059669",
    "warning": "#D97706",
    "error": "#DC2626",
    "info": "#2563EB",
}

STATUS_COLORS = {
    "idea": "#A8A29E",
    "topic_selected": "#3D8B7A",
    "script_ready": "#3D8B7A",
    "storyboard_ready": "#7C3AED",
    "voice_ready": "#9333EA",
    "avatar_ready": "#E07A5F",
    "broll_ready": "#D97706",
    "composing": "#D97706",
    "composed": "#059669",
    "pending_review": "#E07A5F",
    "approved": "#059669",
    "publishing": "#2563EB",
    "published": "#059669",
    "rejected": "#DC2626",
}

# ── Remix Icon 集成 ────────────────────────────────────────

ICON_MAP = {
    "lightbulb": "ri-lightbulb-line",
    "edit": "ri-edit-2-line",
    "rocket": "ri-rocket-2-line",
    "chart": "ri-bar-chart-2-line",
    "settings": "ri-settings-3-line",
    "dashboard": "ri-dashboard-3-line",
    "film": "ri-film-line",
    "play": "ri-play-circle-line",
    "check": "ri-check-line",
    "close": "ri-close-line",
    "clock": "ri-time-line",
    "book": "ri-book-open-line",
    "mic": "ri-mic-line",
    "person": "ri-user-voice-line",
    "camera": "ri-camera-line",
    "layers": "ri-stack-line",
    "send": "ri-send-plane-line",
    "bell": "ri-notification-3-line",
    "warning": "ri-error-warning-line",
    "tiktok": "ri-tiktok-line",
    "wechat": "ri-wechat-line",
    "trophy": "ri-trophy-line",
    "arrow_right": "ri-arrow-right-s-line",
    "add": "ri-add-line",
    "refresh": "ri-refresh-line",
    "download": "ri-download-line",
    "search": "ri-search-line",
    "sparkle": "ri-sparkling-line",
    "clip": "ri-attachment-line",
    "eye": "ri-eye-line",
    "lock": "ri-lock-line",
    "image": "ri-image-line",
    "calendar": "ri-calendar-line",
    "tag": "ri-price-tag-3-line",
    "link": "ri-link",
    "file": "ri-file-text-line",
    "list": "ri-list-check",
}


def icon(name: str, size: str = "md", color: str | None = None) -> str:
    """返回 Remix Icon HTML。size: sm=16 md=20 lg=24 xl=32。"""
    cls = ICON_MAP.get(name, f"ri-{name}")
    sizes = {"sm": "16px", "md": "20px", "lg": "24px", "xl": "32px"}
    px = sizes.get(size, "20px")
    style = f"font-size:{px}; line-height:1;"
    if color:
        style += f" color:{color};"
    return f'<i class="{cls}" style="{style}"></i>'


# ── Logo ────────────────────────────────────────────────────

LOGO_SVG = """<svg viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#E07A5F"/><stop offset="100%" stop-color="#C4613F"/>
  </linearGradient></defs>
  <rect width="36" height="36" rx="10" fill="url(#lg)"/>
  <text x="18" y="24.5" text-anchor="middle" fill="white"
    font-size="17" font-weight="700" font-family="sans-serif">攸</text>
</svg>"""


def render_logo(size: int = 36) -> str:
    return LOGO_SVG.replace('viewBox="0 0 36 36"', f'width="{size}" height="{size}"')


# ── 外部 CDN 资源 ─────────────────────────────────────────

_CDN_LINKS = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/remixicon@4.6.0/fonts/remixicon.css" crossorigin="anonymous">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet">
"""

# ── CSS ─────────────────────────────────────────────────────

_CSS = """
/* ── 字体 ── */
* { font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif; }

:root {
    --yx-primary: #E07A5F;
    --yx-primary-dark: #C4613F;
    --yx-primary-light: #FEF2EE;
    --yx-accent: #3D8B7A;
    --yx-accent-dark: #2D6B5E;
    --yx-accent-light: #EFF8F5;
    --yx-bg: #F8F6F3;
    --yx-bg-deep: #F0EDE8;
    --yx-card: #FFFFFF;
    --yx-fg: #292524;
    --yx-fg-light: #44403C;
    --yx-muted: #78716C;
    --yx-muted-light: #A8A29E;
    --yx-border: #E7E5E4;
    --yx-border-hover: #D6D3D1;
    --yx-success: #059669;
    --yx-warning: #D97706;
    --yx-error: #DC2626;
    --yx-info: #2563EB;
    --yx-radius: 14px;
    --yx-radius-sm: 10px;
    --yx-shadow: 0 1px 2px rgba(0,0,0,0.04);
    --yx-shadow-md: 0 2px 8px rgba(0,0,0,0.06);
    --yx-shadow-hover: 0 4px 16px rgba(0,0,0,0.08);
    --yx-font: 'Noto Sans SC', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
    --yx-transition: all 0.15s ease;
}

/* ── 全局 ── */
.stApp, .stApp > div { font-family: var(--yx-font) !important; }
.stApp { background-color: var(--yx-bg) !important; }

/* 主内容区更宽敞的留白 */
[data-testid="stMainBlockContainer"] {
    padding-top: 2.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: var(--yx-font) !important;
    color: var(--yx-fg) !important;
}

p, span, label, .stMarkdown { color: var(--yx-fg); }

/* ── 隐藏 Streamlit 默认 UI ── */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
footer::after { content: none !important; }
/* 隐藏 Deploy 按钮和主菜单按钮（保留侧边栏展开/折叠按钮） */
[data-testid="stBaseButton-header"] { display: none !important; }
[data-testid="stMainMenuButton"] { display: none !important; }

/* ── 隐藏 "Press enter to apply" 提示 ── */
[data-testid="stTextInputInstructions"] { display: none !important; }
.stTextInput small { display: none !important; }
.stForm [data-testid="stTextInputInstructions"] { display: none !important; }

/* ── 侧边栏 ── */
/* 全局默认显示侧边栏，防止残留 display:none CSS */
section[data-testid="stSidebar"] { display: flex !important; }
[data-testid="stSidebar"] {
    background-color: var(--yx-card) !important;
    border-right: 1px solid var(--yx-border) !important;
}

[data-testid="stSidebarNav"] { padding-top: 0.5rem; }

[data-testid="stSidebarNav"] li a {
    border-radius: var(--yx-radius-sm) !important;
    transition: var(--yx-transition);
    color: var(--yx-muted) !important;
    padding: 0.5rem 0.75rem !important;
    margin: 2px 0 !important;
    font-weight: 500 !important;
}

[data-testid="stSidebarNav"] li a:hover {
    background: var(--yx-primary-light) !important;
    color: var(--yx-primary) !important;
}

[data-testid="stSidebarNav"] li a[aria-current="page"] {
    background: var(--yx-primary) !important;
    color: white !important;
}

/* ── 按钮 ── */
.stButton > button[kind="primary"] {
    background: var(--yx-primary) !important;
    border: none !important;
    border-radius: var(--yx-radius-sm) !important;
    font-weight: 500 !important;
    color: white !important;
    transition: var(--yx-transition);
    box-shadow: var(--yx-shadow) !important;
}

.stButton > button[kind="primary"]:hover {
    background: var(--yx-primary-dark) !important;
    transform: translateY(-1px);
    box-shadow: var(--yx-shadow-md) !important;
}

.stButton > button[kind="primary"]:active { transform: translateY(0); }

.stButton > button[kind="secondary"] {
    border: 1px solid var(--yx-border) !important;
    border-radius: var(--yx-radius-sm) !important;
    color: var(--yx-muted) !important;
    background: var(--yx-card) !important;
    transition: var(--yx-transition);
}

.stButton > button[kind="secondary"]:hover {
    border-color: var(--yx-primary) !important;
    color: var(--yx-primary) !important;
}

/* ── 表单输入 ── */
.stTextInput input,
.stTextArea textarea {
    background-color: var(--yx-card) !important;
    border: 1px solid var(--yx-border) !important;
    color: var(--yx-fg) !important;
    border-radius: var(--yx-radius-sm) !important;
    font-family: var(--yx-font) !important;
    font-size: 16px !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--yx-primary) !important;
    box-shadow: 0 0 0 3px rgba(224,122,95,0.15) !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: var(--yx-muted-light) !important;
}

/* ── 指标 ── */
[data-testid="stMetricValue"] {
    font-size: 2rem !important; font-weight: 700 !important;
    color: var(--yx-fg) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.875rem !important; color: var(--yx-muted) !important;
}
[data-testid="stMetricDelta"] { color: var(--yx-success) !important; }

/* ── Tab 栏（分段控制器风格）── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--yx-bg-deep);
    border-radius: 12px;
    padding: 4px;
    gap: 2px;
    border: 1px solid var(--yx-border);
}
.stTabs [data-baseweb="tab"] {
    color: var(--yx-muted) !important;
    border-radius: 10px !important;
    padding: 0.5rem 1.25rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--yx-fg) !important;
    background: var(--yx-card) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    color: var(--yx-fg-light) !important;
    background: rgba(0,0,0,0.03);
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--yx-card) !important;
    border: 1px solid var(--yx-border) !important;
    border-radius: var(--yx-radius-sm) !important;
    color: var(--yx-fg) !important;
    transition: var(--yx-transition);
    box-shadow: var(--yx-shadow) !important;
}
.streamlit-expanderHeader:hover {
    border-color: var(--yx-primary) !important;
    box-shadow: var(--yx-shadow-md) !important;
}

/* ── Toast ── */
[data-testid="stToast"] {
    background: var(--yx-card) !important;
    border: 1px solid var(--yx-border) !important;
    border-radius: var(--yx-radius-sm) !important;
    box-shadow: var(--yx-shadow-md) !important;
}

/* ── 分隔线 ── */
hr, .stDivider { border-color: var(--yx-border) !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] svg { color: var(--yx-primary) !important; }

/* ── Select / Multiselect / Radio ── */
.stSelectbox div[data-baseweb="select"],
.stMultiSelect div[data-baseweb="select"] {
    background-color: var(--yx-card) !important;
}
.stRadio div[role="radiogroup"] label { color: var(--yx-muted); }
.stRadio div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
    border-color: var(--yx-border) !important;
}

/* ── 表单 ── */
form {
    border: 1px solid var(--yx-border) !important;
    border-radius: var(--yx-radius) !important;
    padding: 1.25rem !important;
    background: var(--yx-card) !important;
    box-shadow: var(--yx-shadow) !important;
}

/* ── Date Input ── */
.stDateInput input {
    background-color: var(--yx-card) !important;
    border: 1px solid var(--yx-border) !important;
    color: var(--yx-fg) !important;
}

/* ── 页面淡入 ── */
@keyframes yxFadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}
.stApp > div:first-child { animation: yxFadeIn 0.25s ease-out; }

/* ── Card 样式（container border） ── */
[data-testid="stVerticalBlock"] > div[style*="border"] {
    border: 1px solid var(--yx-border) !important;
    border-radius: var(--yx-radius) !important;
    background: var(--yx-card) !important;
    padding: 1.25rem !important;
    box-shadow: var(--yx-shadow) !important;
    transition: var(--yx-transition);
}
[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
    box-shadow: var(--yx-shadow-md) !important;
}

/* ── 空状态容器 ── */
.yx-empty-state { text-align: center; padding: 3rem 0; color: var(--yx-muted); }
.yx-empty-state .yx-empty-icon { font-size: 2.5rem; margin-bottom: 0.75rem; color: var(--yx-muted-light); }
.yx-empty-state .yx-empty-title { font-size: 1rem; color: var(--yx-fg); font-weight: 600; }
.yx-empty-state .yx-empty-desc { font-size: 0.85rem; color: var(--yx-muted); margin-top: 0.35rem; }

/* ── 滚动条 ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--yx-bg); }
::-webkit-scrollbar-thumb { background: var(--yx-border-hover); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--yx-muted-light); }

/* ── 移动端适配 ── */
@media screen and (max-width: 768px) {
    [data-testid="stSidebar"] { width: min(280px, 80vw) !important; }
    .stTextInput input, .stTextArea textarea { min-height: 48px !important; }
    .stButton > button { min-height: 48px !important; }
    .yx-task-grid { grid-template-columns: 1fr !important; }
    .yx-stats-grid { grid-template-columns: repeat(2, 1fr) !important; }
    .yx-two-col { flex-direction: column !important; }
    .yx-two-col > * { width: 100% !important; }
    .yx-pipeline-bar { overflow-x: auto; -webkit-overflow-scrolling: touch; }
}

@media screen and (min-width: 769px) and (max-width: 1024px) {
    .yx-task-grid { grid-template-columns: repeat(2, 1fr) !important; }
}

@media screen and (max-width: 932px) and (orientation: landscape) {
    .yx-task-grid { grid-template-columns: 1fr !important; }
}

@supports (-webkit-touch-callout: none) {
    .stButton > button { -webkit-touch-callout: none; -webkit-user-select: none; }
    .stApp { min-height: -webkit-fill-available; }
}

html { -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }
"""


def inject_styles():
    """在页面顶部注入全局自定义 CSS + CDN 资源。"""
    st.markdown(_CDN_LINKS, unsafe_allow_html=True)
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


# ── XSS 防护 ──────────────────────────────────────────────

def esc(value: str | int | float | None) -> str:
    """HTML 转义变量内容，防止 XSS 注入。"""
    if value is None:
        return ""
    return html.escape(str(value))


# ── 共享 UI 组件 ──────────────────────────────────────────

PIPELINE_STAGES = [
    ("idea", "选题"),
    ("topic_selected", "确认"),
    ("script_ready", "脚本"),
    ("storyboard_ready", "分镜"),
    ("voice_ready", "配音"),
    ("avatar_ready", "数字人"),
    ("broll_ready", "B-roll"),
    ("composing", "合成中"),
    ("composed", "已合成"),
    ("pending_review", "待审核"),
    ("approved", "已通过"),
    ("publishing", "发布中"),
    ("published", "已发布"),
]

PIPELINE_ICONS = {
    "idea": "lightbulb", "topic_selected": "check", "script_ready": "book",
    "storyboard_ready": "layers", "voice_ready": "mic", "avatar_ready": "person",
    "broll_ready": "camera", "composing": "layers", "composed": "film",
    "pending_review": "edit", "approved": "check", "publishing": "send",
    "published": "check",
}


def page_header(icon_name: str, title: str, subtitle: str):
    """页面标题组件 — Remix Icon + 标题 + 副标题。"""
    ic = icon(icon_name, "xl", COLORS["primary"])
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1.5rem;
        padding-bottom:1.25rem; border-bottom:2px solid {COLORS['border']};">
        <div style="width:44px; height:44px; border-radius:12px;
            background:{COLORS['primary_light']};
            display:flex; align-items:center; justify-content:center;
            flex-shrink:0;">{ic}</div>
        <div>
            <div style="font-size:1.6rem; font-weight:700; color:{COLORS['fg']};
                letter-spacing:-0.01em; line-height:1.2;">{esc(title)}</div>
            <div style="font-size:0.875rem; color:{COLORS['muted']};
                margin-top:0.2rem;">{esc(subtitle)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def empty_state(icon_name: str, title: str, desc: str):
    """空状态组件 — Remix Icon + 标题 + 描述。"""
    ic = icon(icon_name, "xl", COLORS["muted_light"])
    st.markdown(f"""
    <div class="yx-empty-state">
        <div class="yx-empty-icon">{ic}</div>
        <div class="yx-empty-title">{esc(title)}</div>
        <div class="yx-empty-desc">{esc(desc)}</div>
    </div>
    """, unsafe_allow_html=True)


def pipeline_progress(current_status: str):
    """渲染视频生命周期进度条。"""
    stage_idx = -1
    for i, (status_key, _) in enumerate(PIPELINE_STAGES):
        if status_key == current_status:
            stage_idx = i
            break

    if current_status == "rejected":
        ic = icon("close", "sm", COLORS["error"])
        st.markdown(f"""
        <div style="background:{COLORS['card']}; border-radius:var(--yx-radius); padding:1rem 1.25rem;
            border-left:3px solid {COLORS['error']}; margin-bottom:1rem;
            box-shadow:var(--yx-shadow);">
            <div style="display:flex; align-items:center; gap:0.5rem;">
                {ic}
                <span style="color:{COLORS['error']}; font-weight:600;">已驳回</span>
                <span style="color:{COLORS['muted']}; font-size:0.8rem;">— 需要修改后重新提交</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    segments = []
    for i, (status_key, label) in enumerate(PIPELINE_STAGES):
        color = STATUS_COLORS.get(status_key, COLORS["muted"])
        if i < stage_idx:
            opacity, weight = "0.6", "500"
        elif i == stage_idx:
            opacity, weight = "1", "700"
        else:
            color = COLORS["muted_light"]
            opacity, weight = "0.35", "400"

        dot_size = "8px" if i != stage_idx else "12px"
        dot_html = (
            f'<div style="width:{dot_size}; height:{dot_size}; border-radius:50%; '
            f'background:{color}; opacity:{opacity};"></div>'
        )
        segments.append(
            f'<div style="display:flex; flex-direction:column; align-items:center; gap:0.2rem; flex:1;">'
            f'{dot_html}'
            f'<div style="font-size:0.6rem; color:{color}; opacity:{opacity}; '
            f'font-weight:{weight}; white-space:nowrap;">{esc(label)}</div>'
            f'</div>'
        )

    st.markdown(f"""
    <div style="background:{COLORS['card']}; border-radius:var(--yx-radius); padding:1rem 1.25rem;
        margin-bottom:1rem; border:1px solid {COLORS['border']}; box-shadow:var(--yx-shadow);">
        <div class="yx-pipeline-bar" style="display:flex; align-items:flex-start; gap:0;">
            {''.join(segments)}
        </div>
    </div>
    """, unsafe_allow_html=True)


def badge(text: str, color: str):
    """语义化徽章组件。"""
    return (f'<span style="background:{color}18; color:{color}; padding:3px 10px;'
            f' border-radius:6px; font-size:0.75rem; font-weight:500;'
            f' display:inline-flex; align-items:center; gap:4px;">{esc(text)}</span>')


def section_header(icon_name: str, title: str, accent: str,
                   right: str = ""):
    """区域标题组件 — 带左侧色条的分组标题，增强区域辨识度。"""
    ic = icon(icon_name, "md", accent)
    right_html = f'<div style="font-size:0.8rem; color:{COLORS["muted"]};">{right}</div>' if right else ""
    return f"""
    <div style="display:flex; align-items:center; justify-content:space-between;
        margin-bottom:1rem; padding-bottom:0.75rem;
        border-bottom:1px solid {COLORS['border']};">
        <div style="display:flex; align-items:center; gap:0.6rem;">
            <div style="width:4px; height:22px; border-radius:2px;
                background:{accent}; flex-shrink:0;"></div>
            <div style="font-size:1.05rem; font-weight:600;
                color:{COLORS['fg']};">{ic} {esc(title)}</div>
        </div>
        {right_html}
    </div>
    """


def stat_card(label: str, value: str, accent: str, icon_name: str = "chart"):
    """统计卡片组件。"""
    ic = icon(icon_name, "lg", accent)
    return f"""
    <div style="background:{COLORS['card']}; border-radius:var(--yx-radius); padding:1.25rem;
        border:1px solid {COLORS['border']}; border-left:3px solid {accent};
        box-shadow:var(--yx-shadow);
        transition:var(--yx-transition); max-width:100%; overflow:hidden; box-sizing:border-box;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.75rem;">
            <div style="font-size:0.8rem; color:{COLORS['muted']}; font-weight:500;">{esc(label)}</div>
            <div style="width:36px; height:36px; border-radius:10px; background:{accent}12;
                display:flex; align-items:center; justify-content:center;">{ic}</div>
        </div>
        <div style="font-size:2rem; font-weight:700; color:{COLORS['fg']}; line-height:1;">{esc(value)}</div>
    </div>
    """


def task_card(icon_name: str, count: str, label: str, desc: str,
              accent: str, button_label: str = "查看"):
    """待办任务卡片组件（工作台用）。"""
    ic = icon(icon_name, "xl", accent)
    return f"""
    <div style="background:{COLORS['card']}; border-radius:var(--yx-radius); padding:1.25rem;
        border:1px solid {COLORS['border']}; border-top:3px solid {accent};
        box-shadow:var(--yx-shadow); transition:var(--yx-transition);
        max-width:100%; overflow:hidden; box-sizing:border-box;">
        <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.75rem;">
            <div style="width:40px; height:40px; border-radius:10px; background:{accent}12;
                display:flex; align-items:center; justify-content:center;">{ic}</div>
            <div style="flex:1;">
                <div style="font-size:1.5rem; font-weight:700; color:{COLORS['fg']}; line-height:1.2;">{esc(count)}</div>
                <div style="font-size:0.8rem; color:{COLORS['muted']}; font-weight:500;">{esc(label)}</div>
            </div>
        </div>
        <div style="font-size:0.85rem; color:{COLORS['muted']}; margin-bottom:0.75rem;">{esc(desc)}</div>
    </div>
    """
