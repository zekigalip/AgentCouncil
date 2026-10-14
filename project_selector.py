from dataclasses import dataclass
from pathlib import Path
import datetime
import unicodedata
from typing import Optional, List
from config import SOURCE_DIR
from i18n import t, toggle_lang
from rich.console import Console
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from prompt_toolkit.styles import Style

console = Console()


@dataclass
class ProjectInfo:
    index: int
    name: str
    path: Path
    modified: str
    has_git: bool


def scan_projects() -> List[ProjectInfo]:
    """Scan and list projects under SOURCE_DIR."""
    projects: List[ProjectInfo] = []
    if not SOURCE_DIR.exists():
        return projects

    subdirs = [
        d for d in SOURCE_DIR.iterdir()
        if d.is_dir() and not d.is_symlink() and not d.name.startswith(".") and not d.name.startswith("._")
    ]
    subdirs.sort(key=lambda x: x.name.lower())

    for idx, d in enumerate(subdirs, 1):
        try:
            mtime = datetime.datetime.fromtimestamp(d.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        except Exception:
            mtime = "-"
        has_git = (d / ".git").exists()
        normalized_name = unicodedata.normalize("NFC", d.name)
        projects.append(
            ProjectInfo(
                index=idx,
                name=normalized_name,
                path=d,
                modified=mtime,
                has_git=has_git,
            )
        )
    return projects


def display_projects_table(projects: List[ProjectInfo], filter_text: Optional[str] = None):
    """Render projects in a Rich Table."""
    displayed = projects
    if filter_text:
        term = filter_text.lower()
        displayed = [p for p in projects if term in p.name.lower()]

    title = t(
        f"📂 [bold cyan]Workspace Projects[/bold cyan] ({len(displayed)} shown)",
        f"📂 [bold cyan]Source Projeleri[/bold cyan] ({len(displayed)} adet gösteriliyor)",
    )
    table = Table(
        title=title,
        header_style="bold blue",
        border_style="dim blue",
        expand=False,
    )
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column(t("Project Name", "Proje Adı"), style="bold white")
    table.add_column(t("Last Modified", "Son Değiştirilme"), style="dim", justify="center")
    table.add_column("Git", style="green", justify="center")

    for p in displayed:
        git_badge = "✓ Git" if p.has_git else "-"
        table.add_row(str(p.index), p.name, p.modified, git_badge)

    console.print(table)


def interactive_select_project() -> Optional[ProjectInfo]:
    """Interactive project selector with fuzzy tab completion and language toggle."""
    projects = scan_projects()
    if not projects:
        console.print(
            t(
                f"[red]No projects found in workspace directory ({SOURCE_DIR})![/red]",
                f"[red]Source dizininde ({SOURCE_DIR}) hiç proje bulunamadı![/red]",
            )
        )
        return None

    display_projects_table(projects)

    project_names = [p.name for p in projects]
    completer = FuzzyCompleter(WordCompleter(project_names, ignore_case=True))
    session = PromptSession(completer=completer)

    pt_style = Style.from_dict({
        "prompt": "bold cyan",
    })

    def _print_tips():
        console.print(
            t(
                "\n[dim]Tip: Enter project number or start typing its name and press [bold yellow]TAB[/bold yellow].[/dim]",
                "\n[dim]İpucu: Proje numarasını girebilir veya adını yazıp [bold yellow]TAB[/bold yellow] tuşuna basabilirsiniz.[/dim]",
            )
        )
        console.print(
            t(
                "[dim]Filter: [bold]f <keyword>[/bold] | List all: [bold]list[/bold] | Language (EN/TR): [bold]l[/bold] | Quit: [bold]q[/bold][/dim]\n",
                "[dim]Filtrelemek için: [bold]f <kelime>[/bold] | Tümünü listele: [bold]list[/bold] | Dil (EN/TR): [bold]l[/bold] | Çıkış: [bold]q[/bold][/dim]\n",
            )
        )

    _print_tips()

    while True:
        try:
            choice = session.prompt(
                [("class:prompt", t("🎯 Select a project > ", "🎯 Bir proje seçin > "))],
                style=pt_style,
            ).strip()

            choice = unicodedata.normalize("NFC", choice)

            if not choice:
                continue

            if choice.lower() in ("q", "quit", "exit"):
                return None

            if choice.lower() in ("l", "lang", "language", "dil"):
                new_lang = toggle_lang()
                console.print(
                    t(
                        f"[bold green]🌐 Language switched to: {new_lang.upper()} (English)[/bold green]\n",
                        f"[bold green]🌐 Dil değiştirildi: {new_lang.upper()} (Türkçe)[/bold green]\n",
                    )
                )
                display_projects_table(projects)
                _print_tips()
                continue

            if choice.lower() == "list":
                display_projects_table(projects)
                continue

            if choice.lower().startswith("f "):
                query = choice[2:].strip()
                display_projects_table(projects, filter_text=query)
                continue

            if choice.isdigit():
                num = int(choice)
                match = next((p for p in projects if p.index == num), None)
                if match:
                    return match
                console.print(
                    t(
                        f"[yellow]Invalid number: {num}. (Must be between 1 and {len(projects)})[/yellow]",
                        f"[yellow]Geçersiz numara: {num}. (1 - {len(projects)} arasında olmalı)[/yellow]",
                    )
                )
                continue

            exact_match = next((p for p in projects if p.name.lower() == choice.lower()), None)
            if exact_match:
                return exact_match

            partial_matches = [p for p in projects if choice.lower() in p.name.lower()]
            if len(partial_matches) == 1:
                return partial_matches[0]
            elif len(partial_matches) > 1:
                console.print(
                    t(
                        f"[yellow]Multiple projects match '{choice}':[/yellow]",
                        f"[yellow]'{choice}' için birden fazla proje bulundu:[/yellow]",
                    )
                )
                for pm in partial_matches:
                    console.print(f"  [{pm.index}] {pm.name}")
                console.print(
                    t(
                        "[yellow]Please enter the exact number or full name.[/yellow]",
                        "[yellow]Lütfen listeden numarasını veya tam adını girin.[/yellow]",
                    )
                )
                continue

            console.print(
                t(
                    f"[red]Project '{choice}' not found. Try again or type 'list'.[/red]",
                    f"[red]'{choice}' adında bir proje bulunamadı. Tekrar deneyin veya 'list' yazın.[/red]",
                )
            )

        except (KeyboardInterrupt, EOFError):
            console.print(t("\n[yellow]Selection cancelled.[/yellow]", "\n[yellow]Seçim iptal edildi.[/yellow]"))
            return None
