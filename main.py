#!/usr/bin/env python3
import sys
from typing import List, Dict, Any
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

from ui import print_banner, print_project_header
from project_selector import interactive_select_project, ProjectInfo
from orchestrator import MultiAgentOrchestrator
from history_manager import save_session_history
from role_manager import RoleConfig, display_roles_table, interactive_configure_roles
from i18n import t, toggle_lang

console = Console()


def main():
    print_banner()
    orchestrator = MultiAgentOrchestrator()
    session = PromptSession()
    pt_style = Style.from_dict({
        "prompt": "bold green",
    })

    while True:
        try:
            # 1. Project Selection
            console.print(
                t(
                    "\n[bold cyan]Step 1: Select the Target Project[/bold cyan]",
                    "\n[bold cyan]1. Adım: İncelenecek Projeyi Belirleyin[/bold cyan]",
                )
            )
            project: ProjectInfo = interactive_select_project()
            if not project:
                console.print(
                    t(
                        "[yellow]AgentCouncil terminated. Happy coding![/yellow]",
                        "[yellow]Ajan Sohbeti sonlandırıldı. İyi çalışmalar![/yellow]",
                    )
                )
                break

            print_project_header(project.name, str(project.path))

            # 2. Role Assignment & Pipeline Order
            role_config = RoleConfig()
            display_roles_table(role_config)

            console.print(
                t(
                    "\n[bold]⚙️ Would you like to customize the Council Roles or Pipeline Order?[/bold]",
                    "\n[bold]⚙️ Rol Dağılımını veya İş Akışı Sırasını Değiştirmek İster misiniz?[/bold]",
                )
            )
            console.print(
                t(
                    "  [bold green][Enter][/bold green] Continue with these roles",
                    "  [bold green][Enter][/bold green] Bu rollerle devam et",
                )
            )
            console.print(
                t(
                    "  [bold yellow][c][/bold yellow] Customize roles & pipeline order",
                    "  [bold yellow][c][/bold yellow] Rolleri ve sıralamayı özelleştir/değiştir",
                )
            )
            console.print(
                t(
                    "  [bold cyan][l][/bold cyan] Switch Language (EN ↔ TR)\n",
                    "  [bold cyan][l][/bold cyan] Dili Değiştir (EN ↔ TR)\n",
                )
            )

            role_choice = input(t("Choice [Enter/c/l]: ", "Seçiminiz [Enter/c/l]: ")).strip().lower()
            if role_choice in ("l", "lang", "dil"):
                new_lang = toggle_lang()
                console.print(
                    t(
                        f"[bold green]🌐 Language switched to: {new_lang.upper()} (English)[/bold green]\n",
                        f"[bold green]🌐 Dil değiştirildi: {new_lang.upper()} (Türkçe)[/bold green]\n",
                    )
                )
                display_roles_table(role_config)
            elif role_choice in ("c", "change", "r", "rol", "roller", "2"):
                role_config = interactive_configure_roles(role_config)

            session_turns: List[Dict[str, Any]] = []

            # 3. Project Prompt / Command Loop
            while True:
                console.print(
                    t(
                        "\n[dim]Give the council a task regarding architecture, features, bug fixes, or refactoring.[/dim]",
                        "\n[dim]Takıma projenin mimarisi, kodları, yeni özellikler veya hata tespitiyle ilgili bir görev verin.[/dim]",
                    )
                )
                console.print(
                    t(
                        "[dim]Tip: Type [bold]menu[/bold] for project list, [bold]lang[/bold] to switch EN/TR, or [bold]q[/bold] to quit.[/dim]\n",
                        "[dim]İpucu: Ana menüye dönmek için [bold]menu[/bold], dil için [bold]lang[/bold], çıkmak için [bold]q[/bold] yazabilirsiniz.[/dim]\n",
                    )
                )

                try:
                    prompt_label = t(
                        f"💬 [{project.name}] Your Task > ",
                        f"💬 [{project.name}] Komutunuz > ",
                    )
                    user_command = session.prompt(
                        [("class:prompt", prompt_label)],
                        style=pt_style,
                    ).strip()
                except (KeyboardInterrupt, EOFError):
                    console.print(t("\n[yellow]Interrupted.[/yellow]", "\n[yellow]İşlem durduruldu.[/yellow]"))
                    break

                if not user_command:
                    continue

                if user_command.lower() in ("q", "quit", "exit"):
                    console.print(t("[yellow]Session ended.[/yellow]", "[yellow]Görüşme sonlandırıldı.[/yellow]"))
                    sys.exit(0)

                if user_command.lower() in ("l", "lang", "language", "dil"):
                    new_lang = toggle_lang()
                    console.print(
                        t(
                            f"[bold green]🌐 Language switched to: {new_lang.upper()} (English)[/bold green]",
                            f"[bold green]🌐 Dil değiştirildi: {new_lang.upper()} (Türkçe)[/bold green]",
                        )
                    )
                    continue

                if user_command.lower() == "menu":
                    break

                # 3. Start Council Deliberation
                console.print(
                    t(
                        f"\n[bold]🚀 Council Convening: Starting analysis and coding plan for {project.name}...[/bold]\n",
                        f"\n[bold]🚀 Takım Toplanıyor: {project.name} için analiz ve kodlama başlıyor...[/bold]\n",
                    )
                )
                responses = orchestrator.run_discussion(
                    project_name=project.name,
                    project_path=str(project.path),
                    user_prompt=user_command,
                    role_config=role_config,
                    previous_turns=session_turns,
                )

                turn_data = {
                    "user_prompt": user_command,
                    "responses": responses,
                }
                session_turns.append(turn_data)

                saved_path = save_session_history(project.name, str(project.path), session_turns)
                console.print(
                    t(
                        f"\n[dim]💾 Session report saved: [underline]{saved_path}[/underline][/dim]\n",
                        f"\n[dim]💾 Sohbet oturumu kaydedildi: [underline]{saved_path}[/underline][/dim]\n",
                    )
                )

                # 4. Next Action Selection
                console.print(t("[bold cyan]What would you like to do next?[/bold cyan]", "[bold cyan]Ne yapmak istersiniz?[/bold cyan]"))
                console.print(
                    t(
                        "  [bold green][1][/bold green] 🚀 [bold]Execute Plan[/bold] — Code ➔ Review ➔ Test ➔ UI Check ➔ Deploy",
                        "  [bold green][1][/bold green] 🚀 [bold]Planı Uygula (Execute Plan)[/bold] — Kod ➔ Review ➔ Test ➔ Ekran Testi ➔ Deploy",
                    )
                )
                console.print(
                    t(
                        "  [bold cyan][2][/bold cyan] 💬 Ask a follow-up question / give a new task (Enter)",
                        "  [bold cyan][2][/bold cyan] 💬 Bu projede follow-up soru / yeni görev ver (Enter)",
                    )
                )
                console.print(
                    t(
                        "  [bold yellow][3][/bold yellow] ⚙️ Reconfigure council roles",
                        "  [bold yellow][3][/bold yellow] ⚙️ Rol dağılımını yeniden düzenle",
                    )
                )
                console.print(
                    t(
                        "  [bold blue][4][/bold blue] 📂 Select another project (Menu)",
                        "  [bold blue][4][/bold blue] 📂 Farklı bir proje seç (Menü)",
                    )
                )
                console.print(
                    t(
                        "  [bold red][5][/bold red] 🚪 Quit (q)\n",
                        "  [bold red][5][/bold red] 🚪 Çıkış (q)\n",
                    )
                )

                next_action = input(t("Choice [1/2/3/4/5]: ", "Seçiminiz [1/2/3/4/5]: ")).strip()

                if next_action == "1":
                    plan_texts = []
                    for r in responses:
                        if r.success and r.content:
                            plan_texts.append(f"### {r.name} ({r.role}):\n{r.content}")
                    full_plan_content = "\n\n".join(plan_texts)

                    from execution_engine import PlanExecutor

                    executor = PlanExecutor(role_config=role_config)
                    executor.execute_plan(
                        project_name=project.name,
                        project_path=str(project.path),
                        plan_content=full_plan_content,
                        user_prompt=user_command,
                        role_config=role_config,
                    )

                    console.print(
                        t(
                            "\n[bold cyan]Post-Execution Options:[/bold cyan]",
                            "\n[bold cyan]Uygulama Sonrası Ne Yapmak İstersiniz?[/bold cyan]",
                        )
                    )
                    console.print(
                        t(
                            "  [bold green][1][/bold green] Continue working on this project",
                            "  [bold green][1][/bold green] Bu projede çalışmaya devam et",
                        )
                    )
                    console.print(
                        t(
                            "  [bold yellow][2][/bold yellow] Select another project",
                            "  [bold yellow][2][/bold yellow] Farklı bir proje seç",
                        )
                    )
                    console.print(
                        t(
                            "  [bold red][3][/bold red] Quit\n",
                            "  [bold red][3][/bold red] Çıkış\n",
                        )
                    )
                    sub_action = input(t("Choice [1/2/3]: ", "Seçiminiz [1/2/3]: ")).strip()
                    if sub_action in ("2", "m", "menu"):
                        break
                    elif sub_action in ("3", "q", "exit"):
                        console.print(
                            t(
                                "[yellow]AgentCouncil terminated. Happy coding![/yellow]",
                                "[yellow]Ajan Sohbeti sonlandırıldı. İyi çalışmalar![/yellow]",
                            )
                        )
                        sys.exit(0)
                    else:
                        continue

                elif next_action == "3":
                    role_config = interactive_configure_roles(role_config)
                    continue
                elif next_action in ("4", "m", "menu"):
                    break
                elif next_action in ("5", "q", "exit"):
                    console.print(
                        t(
                            "[yellow]AgentCouncil terminated. Happy coding![/yellow]",
                            "[yellow]Ajan Sohbeti sonlandırıldı. İyi çalışmalar![/yellow]",
                        )
                    )
                    sys.exit(0)
                else:
                    continue

        except KeyboardInterrupt:
            console.print(t("\n[yellow]Exiting...[/yellow]", "\n[yellow]Çıkılıyor...[/yellow]"))
            break
        except Exception as e:
            console.print(
                t(
                    f"\n[red]Unexpected error occurred: {e}[/red]",
                    f"\n[red]Beklenmedik bir hata oluştu: {e}[/red]",
                )
            )
            break


if __name__ == "__main__":
    main()
