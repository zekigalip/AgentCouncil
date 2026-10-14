from dataclasses import dataclass, field
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import PromptSession

from config import AGENTS_META
from i18n import t
from agents import (
    BaseAgent,
    ClaudeAgent,
    CodexAgent,
    CursorAgent,
    GrokAgent,
    AgyAgent,
)

console = Console()


@dataclass
class RoleConfig:
    analyst: str = "claude"     # Architect & Analyst
    coder: str = "codex"        # Lead Developer (Coder)
    reviewer: str = "cursor"    # Senior Reviewer
    security: str = "grok"      # Security & Edge-Case Analyst
    tester: str = "agy"         # QA & Synthesis Lead

    active_steps: List[str] = field(
        default_factory=lambda: [
            "analyst",
            "coder",
            "reviewer",
            "security",
            "tester",
        ]
    )


def get_agent_instances() -> Dict[str, BaseAgent]:
    """Return all available agent instances."""
    return {
        "claude": ClaudeAgent(),
        "codex": CodexAgent(),
        "cursor": CursorAgent(),
        "grok": GrokAgent(),
        "agy": AgyAgent(),
    }


def get_role_info(role_key: str) -> tuple[str, str, str]:
    role_map = {
        "analyst": (
            t("Architect & System Analyst", "Mimar & Sistem Analisti"),
            "🟣",
            t(
                "Analyzes project architecture, requirements, and creates the technical roadmap.",
                "Proje yapısını inceler, ihtiyaçları ve mimari yol haritasını çizer.",
            ),
        ),
        "coder": (
            t("Lead Developer & Coder", "Geliştirici & Kodlama Uzmanı (Coder)"),
            "🟢",
            t(
                "Implements the roadmap into concrete files, functions, and classes.",
                "Planı dosyalara kodlar, fonksiyon/sınıf implementasyonlarını yazar.",
            ),
        ),
        "reviewer": (
            t("Senior Code Reviewer", "Kıdemli Kod İnceleyici (Reviewer)"),
            "🔵",
            t(
                "Audits code quality, refactoring opportunities, clean code, and performance.",
                "Kodu denetler, refactoring, temiz kod ve performans açıklarını inceler.",
            ),
        ),
        "security": (
            t("Security & Edge-Case Analyst", "Güvenlik & Uç Durum Analisti"),
            "🔴",
            t(
                "Audits security vulnerabilities, fault tolerance, and critical edge cases.",
                "Güvenlik açıkları, hata toleransı ve kritik edge-case'leri denetler.",
            ),
        ),
        "tester": (
            t("QA & Synthesis Lead", "Test & Sentez Lideri"),
            "🟡",
            t(
                "Writes/runs tests, resolves council consensus, and delivers the final action plan.",
                "Test kodlarını yazar/koşar, ekip mutabakatını sağlar ve nihai planı sunar.",
            ),
        ),
    }
    return role_map.get(role_key, (role_key, "🤖", ""))


def display_roles_table(config: RoleConfig):
    """Render current role assignments and pipeline order in a Rich Table."""
    table = Table(
        title=t(
            "👥 [bold cyan]Council Role Assignments & Pipeline Order[/bold cyan]",
            "👥 [bold cyan]Görev Dağılımı ve İş Akışı Sıralaması[/bold cyan]",
        ),
        header_style="bold blue",
        border_style="dim blue",
        expand=False,
    )
    table.add_column(t("Step", "Sıra"), justify="center", style="bold cyan")
    table.add_column(t("Role", "Rol"), style="bold white")
    table.add_column(t("Assigned Agent", "Atanan Ajan"), style="bold")
    table.add_column(t("Provider", "Sağlayıcı"), style="dim")
    table.add_column(t("Responsibility", "İşlev Özeti"), style="dim")

    step_order = ["analyst", "coder", "reviewer", "security", "tester"]
    for idx, role_key in enumerate(step_order, 1):
        agent_id = getattr(config, role_key)
        meta = AGENTS_META.get(agent_id, {})
        title, icon, desc = get_role_info(role_key)
        agent_display = f"{meta.get('icon', '🤖')} {meta.get('name', agent_id)}"
        provider = meta.get("provider", "-")
        table.add_row(f"{idx}.", f"{icon} {title}", agent_display, provider, desc)

    console.print(table)


def interactive_configure_roles(current: Optional[RoleConfig] = None) -> RoleConfig:
    """Interactive prompt for customizing council roles step by step."""
    cfg = current or RoleConfig()
    available = ["claude", "codex", "cursor", "grok", "agy"]

    console.print(
        Panel(
            t(
                "[bold yellow]⚙️ Customize Council Roles & Pipeline[/bold yellow]\n"
                "[dim]Select which AI agent handles each stage. "
                "Press [bold]Enter[/bold] to keep the currently assigned agent.[/dim]",
                "[bold yellow]⚙️ Rol ve Görev Dağılımı Düzenleme[/bold yellow]\n"
                "[dim]Her aşama için hangi ajanın görev alacağını seçebilirsiniz. "
                "Değiştirmek istemediğiniz aşamada doğrudan [bold]Enter[/bold]'a basarak mevcut ajanı koruyabilirsiniz.[/dim]",
            ),
            border_style="yellow",
        )
    )

    session = PromptSession()
    step_order = [
        (
            "analyst",
            t("1. Architect & Analyst (Architecture Planning)", "1. Mimar & Analist (Mimari Planlama)"),
        ),
        (
            "coder",
            t("2. Lead Developer / Coder (Implementation)", "2. Geliştirici / Coder (Kod Yazımı)"),
        ),
        (
            "reviewer",
            t("3. Senior Code Reviewer (Code Review)", "3. Kod İnceleyici / Reviewer (Code Review)"),
        ),
        (
            "security",
            t("4. Security & Edge-Case Analyst (Security Audit)", "4. Güvenlik & Uç Durum Analisti (Güvenlik Denetimi)"),
        ),
        (
            "tester",
            t("5. QA & Synthesis Lead (Testing & Final Consensus)", "5. Test & Sentez Lideri (Test ve Nihai Konsensüs)"),
        ),
    ]

    for role_key, role_label in step_order:
        current_agent_id = getattr(cfg, role_key)
        current_meta = AGENTS_META.get(current_agent_id, {})

        console.print(
            f"\n[bold white]{role_label}:[/bold white] "
            f"({t('Current', 'Şu anki')}: [bold cyan]{current_meta.get('name', current_agent_id)}[/bold cyan])"
        )
        for i, a_id in enumerate(available, 1):
            m = AGENTS_META.get(a_id, {})
            marker = (
                f" [green]({t('Current', 'Mevcut')})[/green]" if a_id == current_agent_id else ""
            )
            console.print(f"  [{i}] {m.get('icon', '🤖')} {m.get('name', a_id)} ({m.get('provider', '')}){marker}")

        try:
            choice = session.prompt(
                t("Select [1-5 or Enter=Keep]: ", "Seçiminiz [1-5 veya Enter=Koru]: ")
            ).strip()
            if choice.isdigit() and 1 <= int(choice) <= len(available):
                selected_agent_id = available[int(choice) - 1]
                setattr(cfg, role_key, selected_agent_id)
                console.print(
                    f"  [green]✓ {t('Assigned', 'Atandı')}:[/green] {AGENTS_META[selected_agent_id]['name']}"
                )
            else:
                console.print(
                    f"  [dim]{t('Kept current agent', 'Mevcut ajan korundu')} ({current_meta.get('name')}).[/dim]"
                )
        except (KeyboardInterrupt, EOFError):
            console.print(
                t(
                    "\n[yellow]Customization cancelled, keeping current roles.[/yellow]",
                    "\n[yellow]Düzenleme iptal edildi, mevcut roller korunuyor.[/yellow]",
                )
            )
            break

    console.print(
        t(
            "\n[bold green]✓ Council Role Configuration Saved![/bold green]\n",
            "\n[bold green]✓ Yeni Rol Dağılımı Kaydedildi![/bold green]\n",
        )
    )
    display_roles_table(cfg)
    return cfg
