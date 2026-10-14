from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.table import Table
from agents.base_agent import AgentResponse
from config import AGENTS_META, get_agent_role
from i18n import t, get_lang

console = Console()


def print_banner():
    banner_text = Text()
    banner_text.append("🏛️  ", style="bold yellow")
    banner_text.append(
        t(
            "AGENT COUNCIL — Autonomous Multi-Agent CLI Orchestrator",
            "AGENT COUNCIL / AJAN SOHBETİ — Otonom Çoklu Ajan Orkestratörü",
        ),
        style="bold white",
    )
    banner_text.append(
        t("\nActive Council: ", "\nKatılımcı Ajanlar: "),
        style="dim",
    )
    banner_text.append("🟣 Claude Code  ", style="bold magenta")
    banner_text.append("🟢 OpenAI Codex  ", style="bold green")
    banner_text.append("🔵 Cursor Agent  ", style="bold cyan")
    banner_text.append("🔴 xAI Grok  ", style="bold red")
    banner_text.append("🟡 Google Antigravity", style="bold yellow")
    banner_text.append(
        f"\n🌐 {t('Language', 'Dil')}: {get_lang().upper()} ({t('type [l] to switch EN/TR', 'EN/TR değiştirmek için [l] yazın')})",
        style="dim cyan",
    )

    console.print(Panel(banner_text, border_style="bright_blue", padding=(1, 2)))


def print_project_header(project_name: str, project_path: str):
    header = Table.grid(padding=1)
    header.add_column(style="bold cyan", justify="right")
    header.add_column(style="bold white")
    header.add_row(t("📁 Selected Project:", "📁 Seçilen Proje:"), project_name)
    header.add_row(t("📍 Path:", "📍 Konum:"), project_path)

    console.print(
        Panel(
            header,
            title=f"[bold green]{t('Active Session', 'Aktif Oturum')}[/bold green]",
            border_style="green",
            padding=(0, 2),
        )
    )


def print_agent_response(response: AgentResponse):
    """Render the agent response inside a styled Rich Panel."""
    meta = AGENTS_META.get(response.agent_id, {})
    style = meta.get("style", "bold white")
    border_style = meta.get("border_style", "white")
    icon = meta.get("icon", "🤖")
    role_label = get_agent_role(response.agent_id) or response.role

    title_text = f"{icon} {response.name} — [italic]{role_label}[/italic] ({response.execution_time:.1f}s)"

    if response.is_limited:
        msg = (
            f"[bold yellow]{t('⚠️ QUOTA / SESSION LIMIT NOTICE', '⚠️ KOTA / OTURUM LİMİTİ BİLGİSİ')}[/bold yellow]\n\n"
            f"{response.error}\n\n"
            f"[dim]{t('Other active council agents are seamlessly continuing the workflow.', 'Bu turda diğer aktif ajanlar süreci devralarak devam ediyor.')}[/dim]"
        )
        console.print(Panel(msg, title=title_text, border_style="yellow", padding=(1, 2)))
        return

    if not response.success:
        err_msg = f"[bold red]{t('ERROR:', 'HATA:')}[/bold red] {response.error}"
        console.print(Panel(err_msg, title=title_text, border_style="red", padding=(1, 2)))
        return

    md = Markdown(response.content)
    console.print(
        Panel(
            md,
            title=f"[{style}]{title_text}[/{style}]",
            border_style=border_style,
            padding=(1, 2),
        )
    )


def print_summary_card(responses: list[AgentResponse]):
    """Print the session summary table for participating council agents."""
    table = Table(
        title=t("✨ Council Session & Agent Status Summary", "✨ Oturum ve Ajan Durum Özeti"),
        border_style="dim blue",
        show_header=True,
    )
    table.add_column(t("Agent", "Ajan"), style="bold")
    table.add_column(t("Role", "Rol"), style="dim")
    table.add_column(t("Status", "Durum"), justify="center")
    table.add_column(t("Duration", "Süre"), justify="right")

    for resp in responses:
        if resp.is_limited:
            status = t("[yellow]⚠️ Limit / Auth Needed[/yellow]", "[yellow]⚠️ Limit / Giriş Bekliyor[/yellow]")
        elif resp.success:
            status = t("[green]✓ Completed[/green]", "[green]✓ Başarılı[/green]")
        else:
            status = t("[red]✗ Failed[/red]", "[red]✗ Hata[/red]")
        role_label = get_agent_role(resp.agent_id) or resp.role
        table.add_row(f"{resp.name}", role_label, status, f"{resp.execution_time:.1f}s")

    console.print(table)
