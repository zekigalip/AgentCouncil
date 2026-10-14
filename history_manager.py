from pathlib import Path
import datetime
from typing import List, Dict, Any
from config import HISTORY_DIR, get_agent_role
from i18n import t


def save_session_history(
    project_name: str,
    project_path: str,
    turns: List[Dict[str, Any]],
) -> Path:
    """Save the council deliberation session as a Markdown report."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in project_name)
    file_path = HISTORY_DIR / f"{timestamp}_{safe_name}.md"

    lines = [
        t("# AgentCouncil Session Report", "# Ajan Sohbeti (AgentCouncil) Oturum Raporu"),
        f"- **{t('Date', 'Tarih')}:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **{t('Project', 'Proje')}:** {project_name}",
        f"- **{t('Directory', 'Dizin')}:** `{project_path}`",
        f"- **{t('Council Members', 'Katılan Ajanlar')}:** Claude Code, OpenAI Codex, Cursor Agent, xAI Grok, Google Antigravity (Agy)",
        "",
        "---",
        "",
    ]

    for turn_idx, turn in enumerate(turns, 1):
        user_prompt = turn.get("user_prompt", "")
        lines.append(
            t(
                f"## 👤 User Task (Round {turn_idx})",
                f"## 👤 Kullanıcı Komutu (Tur {turn_idx})",
            )
        )
        lines.append(f"```text\n{user_prompt}\n```")
        lines.append("")

        responses = turn.get("responses", [])
        for resp in responses:
            agent_name = resp.name
            role = get_agent_role(resp.agent_id) or resp.role
            lines.append(f"### 🤖 {agent_name} ({role})")
            if resp.is_limited:
                lines.append(f"> ⚠️ **{t('Session Limit', 'Oturum Limiti')}:** {resp.error}")
            elif not resp.success:
                lines.append(f"> ❌ **{t('Error', 'Hata')}:** {resp.error}")
            else:
                lines.append(resp.content)
            lines.append("")
        lines.append("---")
        lines.append("")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return file_path
