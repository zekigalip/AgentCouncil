import os
from pathlib import Path
import shutil
from i18n import t

# Base Directories / Temel Dizinler
APP_DIR = Path(__file__).parent.resolve()
SOURCE_DIR = Path(
    os.environ.get("AGENT_COUNCIL_SOURCE_DIR")
    or os.environ.get("AJAN_SOURCE_DIR")
    or str(APP_DIR.parent)
).resolve()
HISTORY_DIR = APP_DIR / "history"
HOME_DIR = Path.home()

# CLI Binary Paths / CLI Komut Yolları
CLAUDE_BIN = shutil.which("claude") or str(HOME_DIR / ".local/bin/claude")
CODEX_BIN = shutil.which("codex") or str(HOME_DIR / ".local/bin/codex")
CURSOR_BIN = shutil.which("cursor-agent") or shutil.which("cursor") or str(HOME_DIR / ".local/bin/cursor-agent")
AGY_BIN = shutil.which("agy") or str(HOME_DIR / ".local/bin/agy")
GROK_BIN = shutil.which("grok") or str(HOME_DIR / ".grok/bin/grok")
QWEN_BIN = shutil.which("qwen") or str(HOME_DIR / ".local/bin/qwen")
MUSE_BIN = shutil.which("muse") or str(HOME_DIR / ".local/bin/muse")
HERMES_BIN = shutil.which("hermes") or str(HOME_DIR / ".local/bin/hermes")

# Agent Definitions / Ajan Tanımları
AGENTS_META = {
    "claude": {
        "id": "claude",
        "name": "Claude Code",
        "provider": "Anthropic",
        "role": "Architect & System Analyst",
        "role_en": "Architect & System Analyst",
        "role_tr": "Mimar & Sistem Analisti",
        "icon": "🟣",
        "style": "bold magenta",
        "border_style": "magenta",
        "bin": CLAUDE_BIN,
        "default_active": True,
    },
    "codex": {
        "id": "codex",
        "name": "OpenAI Codex",
        "provider": "OpenAI",
        "role": "Lead Developer & Coding Specialist",
        "role_en": "Lead Developer & Coding Specialist",
        "role_tr": "Geliştirici & Kodlama Uzmanı",
        "icon": "🟢",
        "style": "bold green",
        "border_style": "green",
        "bin": CODEX_BIN,
        "default_active": True,
    },
    "cursor": {
        "id": "cursor",
        "name": "Cursor Agent",
        "provider": "Cursor",
        "role": "Senior Code Reviewer & Optimizer",
        "role_en": "Senior Code Reviewer & Optimizer",
        "role_tr": "Kıdemli Kod İnceleyici & Optimizasyon",
        "icon": "🔵",
        "style": "bold cyan",
        "border_style": "cyan",
        "bin": CURSOR_BIN,
        "default_active": True,
    },
    "agy": {
        "id": "agy",
        "name": "Google Antigravity (Agy)",
        "provider": "Google DeepMind",
        "role": "Principal Engineer, QA & Synthesis Lead",
        "role_en": "Principal Engineer, QA & Synthesis Lead",
        "role_tr": "Baş Mühendis, Test & Sentez Lideri",
        "icon": "🟡",
        "style": "bold yellow",
        "border_style": "yellow",
        "bin": AGY_BIN,
        "default_active": True,
    },
    "grok": {
        "id": "grok",
        "name": "xAI Grok",
        "provider": "xAI",
        "role": "Security & Edge-Case Analyst",
        "role_en": "Security & Edge-Case Analyst",
        "role_tr": "Güvenlik & Uç Durum Analisti",
        "icon": "🔴",
        "style": "bold red",
        "border_style": "red",
        "bin": GROK_BIN,
        "default_active": True,
    },
    "qwen": {
        "id": "qwen",
        "name": "Alibaba Qwen",
        "provider": "Alibaba Cloud",
        "role": "Performance & Algorithm Specialist",
        "role_en": "Performance & Algorithm Specialist",
        "role_tr": "Performans & Algoritma Uzmanı",
        "icon": "🟠",
        "style": "bold bright_yellow",
        "border_style": "bright_yellow",
        "bin": QWEN_BIN,
        "default_active": False,
    },
    "muse": {
        "id": "muse",
        "name": "Meta AI Muse",
        "provider": "Meta AI",
        "role": "Infrastructure & Framework Specialist",
        "role_en": "Infrastructure & Framework Specialist",
        "role_tr": "Altyapı & Framework Uzmanı",
        "icon": "🔷",
        "style": "bold blue",
        "border_style": "blue",
        "bin": MUSE_BIN,
        "default_active": False,
    },
    "hermes": {
        "id": "hermes",
        "name": "Hermes Agent",
        "provider": "Hermes / Nous",
        "role": "Autonomous Integration & Tooling Specialist",
        "role_en": "Autonomous Integration & Tooling Specialist",
        "role_tr": "Otonom Entegrasyon & Araç Uzmanı",
        "icon": "⚪",
        "style": "bold white",
        "border_style": "white",
        "bin": HERMES_BIN,
        "default_active": False,
    },
}


def get_agent_role(agent_id: str) -> str:
    meta = AGENTS_META.get(agent_id, {})
    return t(meta.get("role_en", meta.get("role", "")), meta.get("role_tr", meta.get("role", "")))


# Timeout (Seconds) / Zaman Aşımı (Saniye)
TIMEOUT_SECONDS = 300
