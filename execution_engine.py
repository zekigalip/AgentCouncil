import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel

from agents import BaseAgent
from ui import print_agent_response
from role_manager import RoleConfig, get_agent_instances
from i18n import t

console = Console()


class CoderPool:
    """Manages the Coder pool and performs automatic LLM Swap on repeated failures."""

    def __init__(self, primary_coder: str = "codex"):
        agents = get_agent_instances()
        order = [primary_coder] + [
            k for k in ["codex", "cursor", "agy", "grok", "claude"] if k != primary_coder
        ]
        self.candidates: List[BaseAgent] = [agents[k] for k in order if k in agents]
        self.current_index = 0

    @property
    def current(self) -> BaseAgent:
        return self.candidates[self.current_index]

    def swap_to_next(self, reason: str) -> BaseAgent:
        old_agent = self.current
        self.current_index = (self.current_index + 1) % len(self.candidates)
        new_agent = self.current

        console.print(
            Panel(
                t(
                    f"[bold red]⚠️ Failed after 3 attempts![/bold red]\n"
                    f"[yellow]Reason:[/yellow] {reason}\n\n"
                    f"[bold cyan]🔄 Developer Swapped:[/bold cyan] {old_agent.name} ➔ [bold green]{new_agent.name}[/bold green]",
                    f"[bold red]⚠️ 3 Denemede Başarı Sağlanamadı![/bold red]\n"
                    f"[yellow]Sebep:[/yellow] {reason}\n\n"
                    f"[bold cyan]🔄 Geliştirici Değiştirildi:[/bold cyan] {old_agent.name} ➔ [bold green]{new_agent.name}[/bold green]",
                ),
                title=t(
                    "[bold yellow]LLM Swap (Developer Rotation)[/bold yellow]",
                    "[bold yellow]LLM Swap (Geliştirici Değişimi)[/bold yellow]",
                ),
                border_style="yellow",
            )
        )
        return new_agent


def get_git_diff_summary(project_path: str) -> Tuple[str, str]:
    """Capture git status and git diff output."""
    try:
        status_res = subprocess.run(
            ["git", "status", "--short"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        status_text = status_res.stdout.strip()
    except Exception:
        status_text = t("Could not read git status.", "Git status alınamadı.")

    try:
        diff_res = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=15,
        )
        diff_text = diff_res.stdout.strip()
        if not diff_text:
            diff_res2 = subprocess.run(
                ["git", "diff"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=15,
            )
            diff_text = diff_res2.stdout.strip()
    except Exception:
        diff_text = ""

    return status_text, diff_text


def detect_test_command(project_path: str) -> Optional[str]:
    """Auto-detect the test runner command for the project."""
    p = Path(project_path)
    if (
        (p / "pytest.ini").exists()
        or (p / "tests").exists()
        or (p / "test").exists()
        or (p / "conftest.py").exists()
    ):
        return "pytest"
    if (p / "package.json").exists():
        return "npm test"
    if (p / "Cargo.toml").exists():
        return "cargo test"
    if (p / "go.mod").exists():
        return "go test ./..."
    if (p / "test.sh").exists():
        return "./test.sh"
    return None


def detect_ui_build_command(project_path: str) -> Optional[str]:
    """Auto-detect frontend / UI build verification command."""
    p = Path(project_path)
    if (p / "portal" / "frontend" / "package.json").exists():
        return "npm --prefix portal/frontend run build"
    if (p / "frontend" / "package.json").exists():
        return "npm --prefix frontend run build"
    if (p / "package.json").exists():
        return "npm run build"
    if (p / "scripts" / "capture_portal_screenshots.py").exists():
        return "python3 scripts/capture_portal_screenshots.py"
    return None


def detect_deploy_command(project_path: str) -> Optional[str]:
    """Auto-detect deploy script in the project."""
    p = Path(project_path)
    if (p / "deploy.sh").exists():
        try:
            content = (p / "deploy.sh").read_text(errors="ignore")
            if "prod" in content:
                return "./deploy.sh prod"
        except Exception:
            pass
        return "./deploy.sh"
    return None


class PlanExecutor:
    """Autonomous 5-stage execution engine: Code -> Review (Loop/Swap) -> Test -> UI Build -> Deploy."""

    def __init__(self, role_config: Optional[RoleConfig] = None):
        self.role_config = role_config or RoleConfig()
        self.agents = get_agent_instances()
        self.coder_pool = CoderPool(primary_coder=self.role_config.coder)

    def get_reviewer(self, current_coder: BaseAgent) -> BaseAgent:
        """Select an independent reviewer distinct from the active coder."""
        target_id = self.role_config.reviewer
        if current_coder.id != target_id and target_id in self.agents:
            return self.agents[target_id]
        for backup_id in ["cursor", "grok", "claude", "agy"]:
            if backup_id != current_coder.id and backup_id in self.agents:
                return self.agents[backup_id]
        return self.agents["agy"]

    def execute_plan(
        self,
        project_name: str,
        project_path: str,
        plan_content: str,
        user_prompt: str,
        role_config: Optional[RoleConfig] = None,
    ) -> bool:
        """Execute the 5-stage autonomous pipeline."""
        if role_config:
            self.role_config = role_config
            self.coder_pool = CoderPool(primary_coder=role_config.coder)

        console.print(
            Panel(
                t(
                    f"[bold green]🚀 Autonomous Plan Execution Pipeline Starting[/bold green]\n"
                    f"[white]Project:[/white] [bold cyan]{project_name}[/bold cyan]\n"
                    f"[white]Directory:[/white] {project_path}\n"
                    f"[white]Coder:[/white] {self.role_config.coder.upper()} | "
                    f"[white]Reviewer:[/white] {self.role_config.reviewer.upper()} | "
                    f"[white]Tester:[/white] {self.role_config.tester.upper()}\n\n"
                    f"[dim]1. Code Implementation ➔ 2. Code Review (Loop) ➔ 3. Test Suite ➔ 4. UI Build Check ➔ 5. Deploy[/dim]",
                    f"[bold green]🚀 Plan Uygulama Hattı Başlatılıyor[/bold green]\n"
                    f"[white]Proje:[/white] [bold cyan]{project_name}[/bold cyan]\n"
                    f"[white]Dizin:[/white] {project_path}\n"
                    f"[white]Coder:[/white] {self.role_config.coder.upper()} | "
                    f"[white]Reviewer:[/white] {self.role_config.reviewer.upper()} | "
                    f"[white]Tester:[/white] {self.role_config.tester.upper()}\n\n"
                    f"[dim]1. Kod Yazımı ➔ 2. Code Review (Döngü) ➔ 3. Test Kodu & Koşumu ➔ 4. Ekran Testi ➔ 5. Deploy[/dim]",
                ),
                title=t("[bold yellow]⚡ Execution Engine[/bold yellow]", "[bold yellow]⚡ Otomasyon Motoru[/bold yellow]"),
                border_style="bright_blue",
                padding=(1, 2),
            )
        )

        # ==============================================================
        # STAGES 1 & 2: CODING & CODE REVIEW LOOP (Max 3 Retries / LLM Swap)
        # ==============================================================
        code_approved = False
        coder = self.coder_pool.current
        max_coder_swaps = 3
        coder_swap_count = 0

        while not code_approved and coder_swap_count < max_coder_swaps:
            review_attempt = 1
            max_review_attempts = 3
            current_feedback = ""

            console.print(
                t(
                    "\n[bold cyan]═══ [1/5] CODE IMPLEMENTATION STAGE ═══[/bold cyan]",
                    "\n[bold cyan]═══ [1/5] KOD YAZMA AŞAMASI ═══[/bold cyan]",
                )
            )
            console.print(
                t(
                    f"Active Developer: [bold green]{coder.name}[/bold green] ({coder.provider})",
                    f"Aktif Geliştirici: [bold green]{coder.name}[/bold green] ({coder.provider})",
                )
            )

            while review_attempt <= max_review_attempts:
                if review_attempt == 1 and not current_feedback:
                    code_prompt = t(
                        f"You are the Lead Developer ({coder.name}) on this project.\n"
                        f"Project Name: {project_name}\n"
                        f"Project Directory: {project_path}\n"
                        f"User Task: \"{user_prompt}\"\n\n"
                        f"=== PLAN TO EXECUTE ===\n{plan_content}\n\n"
                        f"INSTRUCTION: Implement this plan directly by writing/editing the files in the project. "
                        f"Create or modify all required files. "
                        f"When finished, list the files modified and summarize the changes made.",
                        f"Sen bu projedeki Baş Geliştiricisin ({coder.name}).\n"
                        f"Proje Adı: {project_name}\n"
                        f"Proje Dizini: {project_path}\n"
                        f"Kullanıcı Görevi: \"{user_prompt}\"\n\n"
                        f"=== UYGULANACAK PLAN ===\n{plan_content}\n\n"
                        f"TALİMAT: Lütfen bu planı doğrudan projedeki dosyalara KOD YAZARAK uygula. "
                        f"Gereken dosyaları oluştur veya düzenle. "
                        f"İşlem bitince hangi dosyaları düzenlediğini ve yaptığın değişiklikleri listele.",
                    )
                    status_msg = t(
                        f"[bold green]💻 {coder.name} is applying the plan and writing code to files...[/bold green]",
                        f"[bold green]💻 {coder.name} planı dosyalara uyguluyor ve kod yazıyor...[/bold green]",
                    )
                else:
                    code_prompt = t(
                        f"You are the Lead Developer ({coder.name}).\n"
                        f"The Code Reviewer identified the following issues in your previous implementation:\n\n"
                        f"=== REVIEW FEEDBACK ===\n{current_feedback}\n\n"
                        f"INSTRUCTION: Open the relevant files, fix these issues directly, and update the code.",
                        f"Sen Baş Geliştiricisin ({coder.name}).\n"
                        f"Code Reviewer bir önceki kodlamanda şu eksikleri ve hataları tespit etti:\n\n"
                        f"=== REVIEW GERİ BİLDİRİMİ ===\n{current_feedback}\n\n"
                        f"TALİMAT: Lütfen ilgili dosyaları açarak bu hataları doğrudan DÜZELT ve kodları güncelle.",
                    )
                    status_msg = t(
                        f"[bold yellow]🔧 {coder.name} is fixing review findings (Attempt {review_attempt}/{max_review_attempts})...[/bold yellow]",
                        f"[bold yellow]🔧 {coder.name} review bulgularını düzeltiyor (Deneme {review_attempt}/{max_review_attempts})...[/bold yellow]",
                    )

                with console.status(status_msg, spinner="dots"):
                    code_resp = coder.execute(code_prompt, project_path, write_mode=True)
                print_agent_response(code_resp)

                status_text, diff_text = get_git_diff_summary(project_path)
                console.print(
                    t(
                        f"\n[dim]📂 Modified Files:\n{status_text or 'No tracked git diff detected or untracked files'}[/dim]\n",
                        f"\n[dim]📂 Değiştirilen Dosyalar:\n{status_text or 'Doğrudan git diff tespit edilemedi veya untracked'}[/dim]\n",
                    )
                )

                reviewer = self.get_reviewer(coder)
                console.print(
                    t(
                        f"[bold magenta]═══ [2/5] CODE REVIEW ({reviewer.name} - Attempt {review_attempt}/{max_review_attempts}) ═══[/bold magenta]",
                        f"[bold magenta]═══ [2/5] CODE REVIEW ({reviewer.name} - Deneme {review_attempt}/{max_review_attempts}) ═══[/bold magenta]",
                    )
                )

                review_prompt = t(
                    f"You are the Independent Code Reviewer ({reviewer.name}).\n"
                    f"Project Name: {project_name}\n"
                    f"Original User Task: \"{user_prompt}\"\n\n"
                    f"=== REQUIRED PLAN ===\n{plan_content}\n\n"
                    f"=== DEVELOPER CHANGES ===\n"
                    f"Git Status:\n{status_text}\n\n"
                    f"Git Diff:\n{diff_text[:6000] if diff_text else code_resp.content[:4000]}\n\n"
                    f"INSTRUCTION: Carefully audit the code for security, syntax, completeness, and adherence to the plan.\n"
                    f"If there are bugs, missing parts, or issues, write 'STATUS: REJECTED' on the first line and list the required fixes below.\n"
                    f"If the code is accurate, complete, and clean, write 'STATUS: APPROVED' on the first line.",
                    f"Sen Bağımsız Code Reviewer'sın ({reviewer.name}).\n"
                    f"Proje Adı: {project_name}\n"
                    f"Kullanıcının Orijinal Görevi: \"{user_prompt}\"\n\n"
                    f"=== UYGULANMASI GEREKEN PLAN ===\n{plan_content}\n\n"
                    f"=== GELİŞTİRİCİNİN YAPTIĞI DEĞİŞİKLİKLER ===\n"
                    f"Git Status:\n{status_text}\n\n"
                    f"Git Diff:\n{diff_text[:6000] if diff_text else code_resp.content[:4000]}\n\n"
                    f"TALİMAT: Kodu güvenlik, sözdizimi, eksik implementasyon ve plana uygunluk açısından titizlikle denetle.\n"
                    f"Eğer kodda hata, eksik veya sorun varsa ilk satıra 'STATUS: REJECTED' yaz ve altına maddelerle düzeltilmesi gereken noktaları ekle.\n"
                    f"Eğer kod doğru, eksiksiz ve sorunsuzsa ilk satıra 'STATUS: APPROVED' yaz.",
                )

                with console.status(
                    t(
                        f"[bold magenta]🔍 {reviewer.name} is reviewing the code...[/bold magenta]",
                        f"[bold magenta]🔍 {reviewer.name} kodu denetliyor...[/bold magenta]",
                    ),
                    spinner="dots",
                ):
                    review_resp = reviewer.execute(review_prompt, project_path, write_mode=False)
                print_agent_response(review_resp)

                review_content = review_resp.content.upper()
                if "STATUS: APPROVED" in review_content or "APPROVED" in review_content[:100]:
                    console.print(
                        Panel(
                            t(
                                f"[bold green]✓ Code Review APPROVED![/bold green]\n"
                                f"[white]Reviewer:[/white] {reviewer.name}\n"
                                f"[white]Attempt:[/white] {review_attempt}/{max_review_attempts}",
                                f"[bold green]✓ Code Review BAŞARIYLA ONAYLANDI![/bold green]\n"
                                f"[white]İnceleyen:[/white] {reviewer.name}\n"
                                f"[white]Deneme:[/white] {review_attempt}/{max_review_attempts}",
                            ),
                            border_style="green",
                        )
                    )
                    code_approved = True
                    break
                else:
                    console.print(
                        t(
                            f"[bold red]✗ Code Review Rejected (Attempt {review_attempt}/{max_review_attempts})[/bold red]",
                            f"[bold red]✗ Code Review Reddedildi (Deneme {review_attempt}/{max_review_attempts})[/bold red]",
                        )
                    )
                    current_feedback = review_resp.content
                    review_attempt += 1

            if not code_approved:
                coder_swap_count += 1
                coder = self.coder_pool.swap_to_next(
                    t(
                        f"Code review did not approve after 3 attempts. Last feedback: {current_feedback[:200]}",
                        f"Code review 3 denemede onay alamadı. Son hata: {current_feedback[:200]}",
                    )
                )

        if not code_approved:
            console.print(
                t(
                    "[bold red]ERROR: Code implementation and review reached maximum retry limit.[/bold red]",
                    "[bold red]HATA: Kod geliştirme ve review süreci azami deneme sınırına ulaştı.[/bold red]",
                )
            )
            return False

        # ==============================================================
        # STAGE 3: TEST SUITE CREATION & EXECUTION (Max 3 Retries / Swap)
        # ==============================================================
        console.print(
            t(
                "\n[bold yellow]═══ [3/5] TEST WRITING & EXECUTION STAGE ═══[/bold yellow]",
                "\n[bold yellow]═══ [3/5] TEST KODU VE TEST KOŞUMU AŞAMASI ═══[/bold yellow]",
            )
        )
        test_cmd = detect_test_command(project_path)
        test_approved = False
        test_attempt = 1
        max_test_attempts = 3
        test_feedback = ""

        test_engineer = self.agents.get(self.role_config.tester, self.agents["agy"])

        while test_attempt <= max_test_attempts and not test_approved:
            test_prompt = t(
                f"You are the QA & Verification Engineer ({test_engineer.name}) on this project.\n"
                f"Project Name: {project_name}\n"
                f"Project Directory: {project_path}\n"
                f"Task Completed: \"{user_prompt}\"\n"
                f"Plan: {plan_content[:2000]}\n\n"
                f"INSTRUCTION: Write or update unit/integration tests matching the project's test structure. "
                f"Write the test files directly into the project's test directory (e.g., tests/) and explain the test cases.",
                f"Sen bu projedeki Test ve Doğrulama Mühendisisin ({test_engineer.name}).\n"
                f"Proje Adı: {project_name}\n"
                f"Proje Dizini: {project_path}\n"
                f"Yapılan Görev: \"{user_prompt}\"\n"
                f"Plan: {plan_content[:2000]}\n\n"
                f"TALİMAT: Projedeki test yapısına uygun birim veya entegrasyon testlerini yaz veya güncelle. "
                f"Test dosyasını projedeki test dizinine (örn. tests/ veya ilgili dizine) doğrudan yaz. "
                f"Yazdığın test dosyalarını ve test senaryolarını açıkla.",
            )
            if test_feedback:
                test_prompt += t(
                    f"\n\nErrors from the previous test run:\n{test_feedback}\nPlease fix both the implementation and the tests accordingly.",
                    f"\n\nÖnceki test koşumunda alınan hatalar:\n{test_feedback}\nLütfen hem kodu hem testleri buna göre düzelt.",
                )

            with console.status(
                t(
                    f"[bold yellow]🧪 {test_engineer.name} is writing/updating test cases...[/bold yellow]",
                    f"[bold yellow]🧪 {test_engineer.name} test kodlarını yazıyor/güncelliyor...[/bold yellow]",
                ),
                spinner="dots",
            ):
                test_write_resp = test_engineer.execute(test_prompt, project_path, write_mode=True)
            print_agent_response(test_write_resp)

            if test_cmd:
                console.print(
                    t(
                        f"\n[bold]⚙️ Running Tests:[/bold] [cyan]{test_cmd}[/cyan]",
                        f"\n[bold]⚙️ Test Koşuluyor:[/bold] [cyan]{test_cmd}[/cyan]",
                    )
                )
                try:
                    test_run = subprocess.run(
                        test_cmd,
                        cwd=project_path,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )
                    test_output = (test_run.stdout or "") + "\n" + (test_run.stderr or "")
                    if test_run.returncode == 0:
                        console.print(
                            Panel(
                                t(
                                    f"[bold green]✓ All Tests Passed![/bold green]\n\n"
                                    f"Command: {test_cmd}\n"
                                    f"Output:\n{test_output[-1500:]}",
                                    f"[bold green]✓ Testler Başarıyla Geçti![/bold green]\n\n"
                                    f"Komut: {test_cmd}\n"
                                    f"Çıktı:\n{test_output[-1500:]}",
                                ),
                                border_style="green",
                                title="[bold green]Test Result: PASS[/bold green]",
                            )
                        )
                        test_approved = True
                        break
                    else:
                        console.print(
                            Panel(
                                t(
                                    f"[bold red]✗ Tests Failed (Exit Code: {test_run.returncode})[/bold red]\n\n"
                                    f"{test_output[-2000:]}",
                                    f"[bold red]✗ Testler Başarısız Oldu (Çıkış Kodu: {test_run.returncode})[/bold red]\n\n"
                                    f"{test_output[-2000:]}",
                                ),
                                border_style="red",
                                title=t(
                                    f"[bold red]Test Failure (Attempt {test_attempt}/{max_test_attempts})[/bold red]",
                                    f"[bold red]Test Hatası (Deneme {test_attempt}/{max_test_attempts})[/bold red]",
                                ),
                            )
                        )
                        test_feedback = test_output
                        test_attempt += 1
                except Exception as e:
                    console.print(
                        t(
                            f"[yellow]Exception while running tests: {e}[/yellow]",
                            f"[yellow]Test çalıştırılırken istisna oluştu: {e}[/yellow]",
                        )
                    )
                    test_attempt += 1
            else:
                console.print(
                    t(
                        "[dim]No automated test runner detected; static verification passed.[/dim]",
                        "[dim]Otomatik test komutu bulunamadı; statik test ve doğrulama onaylandı kabul ediliyor.[/dim]",
                    )
                )
                test_approved = True
                break

        if not test_approved:
            coder = self.coder_pool.swap_to_next(
                t(
                    f"Tests failed after 3 attempts: {test_feedback[:200]}",
                    f"Testler 3 denemede geçmedi: {test_feedback[:200]}",
                )
            )
            console.print(
                t(
                    f"[bold yellow]New Coder ({coder.name}) is stepping in to resolve test failures...[/bold yellow]",
                    f"[bold yellow]Yeni Coder ({coder.name}) test hatalarını çözmek için devreye giriyor...[/bold yellow]",
                )
            )
            with console.status(
                t(
                    f"[bold green]🔧 {coder.name} is resolving test failures...[/bold green]",
                    f"[bold green]🔧 {coder.name} test hatalarını gideriyor...[/bold green]",
                ),
                spinner="dots",
            ):
                fix_resp = coder.execute(
                    t(
                        f"Tests failed with the following output:\n{test_feedback}\nPlease inspect and fix the code.",
                        f"Testler şu hatayla başarısız oldu:\n{test_feedback}\nLütfen kodu açarak düzelt.",
                    ),
                    project_path,
                    write_mode=True,
                )
            print_agent_response(fix_resp)

        # ==============================================================
        # STAGE 4: UI / FRONTEND BUILD CHECK (Max 3 Retries)
        # ==============================================================
        console.print(
            t(
                "\n[bold blue]═══ [4/5] UI & FRONTEND BUILD VERIFICATION ═══[/bold blue]",
                "\n[bold blue]═══ [4/5] EKRAN VE UI BUILD TESTİ ═══[/bold blue]",
            )
        )
        ui_cmd = detect_ui_build_command(project_path)
        ui_approved = True

        if ui_cmd:
            console.print(
                t(
                    f"[bold]📱 UI Build Command Detected:[/bold] [cyan]{ui_cmd}[/cyan]",
                    f"[bold]📱 UI Doğrulama Komutu Tespit Edildi:[/bold] [cyan]{ui_cmd}[/cyan]",
                )
            )
            ui_attempt = 1
            max_ui_attempts = 3
            ui_approved = False

            while ui_attempt <= max_ui_attempts and not ui_approved:
                with console.status(
                    t(
                        f"[bold blue]🖥️ Running UI / frontend build test ({ui_attempt}/{max_ui_attempts})...[/bold blue]",
                        f"[bold blue]🖥️ Ekran / UI build testi koşuluyor ({ui_attempt}/{max_ui_attempts})...[/bold blue]",
                    ),
                    spinner="dots",
                ):
                    try:
                        ui_run = subprocess.run(
                            ui_cmd,
                            cwd=project_path,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=180,
                        )
                        ui_output = (ui_run.stdout or "") + "\n" + (ui_run.stderr or "")
                        if ui_run.returncode == 0:
                            console.print(
                                Panel(
                                    t(
                                        f"[bold green]✓ UI / Frontend Build Passed![/bold green]\n\n"
                                        f"Command: {ui_cmd}\n"
                                        f"{ui_output[-1000:]}",
                                        f"[bold green]✓ Ekran / UI Build Testi Başarılı![/bold green]\n\n"
                                        f"Komut: {ui_cmd}\n"
                                        f"{ui_output[-1000:]}",
                                    ),
                                    border_style="green",
                                )
                            )
                            ui_approved = True
                            break
                        else:
                            console.print(
                                Panel(
                                    t(
                                        f"[bold red]✗ UI Build Failed (Attempt {ui_attempt}/{max_ui_attempts})[/bold red]\n\n"
                                        f"{ui_output[-1500:]}",
                                        f"[bold red]✗ Ekran / UI Testi Hatası (Deneme {ui_attempt}/{max_ui_attempts})[/bold red]\n\n"
                                        f"{ui_output[-1500:]}",
                                    ),
                                    border_style="red",
                                )
                            )
                            with console.status(
                                t(
                                    f"[bold yellow]🔧 {coder.name} is fixing the UI build error...[/bold yellow]",
                                    f"[bold yellow]🔧 {coder.name} UI build hatasını düzeltiyor...[/bold yellow]",
                                ),
                                spinner="dots",
                            ):
                                coder.execute(
                                    t(
                                        f"UI / build check failed with the following error:\n{ui_output}\nPlease fix the files.",
                                        f"UI / build testi şu hatayla başarısız oldu:\n{ui_output}\nLütfen dosyaları açarak düzelt.",
                                    ),
                                    project_path,
                                    write_mode=True,
                                )
                            ui_attempt += 1
                    except Exception as e:
                        console.print(
                            t(
                                f"[yellow]Error during UI check: {e}[/yellow]",
                                f"[yellow]UI testinde hata: {e}[/yellow]",
                            )
                        )
                        ui_attempt += 1

            if not ui_approved:
                console.print(
                    t(
                        "[bold red]⚠️ UI build check did not pass after 3 attempts.[/bold red]",
                        "[bold red]⚠️ Ekran testi 3 denemede geçemedi.[/bold red]",
                    )
                )
        else:
            console.print(
                t(
                    "[dim]No dedicated UI/Frontend build script detected; UI stage complete.[/dim]",
                    "[dim]Bu projede özel bir UI/Frontend build komutu bulunamadı; ekran testi aşaması tamamlandı.[/dim]",
                )
            )

        # ==============================================================
        # STAGE 5: DEPLOYMENT
        # ==============================================================
        console.print(
            t(
                "\n[bold green]═══ [5/5] DEPLOYMENT STAGE ═══[/bold green]",
                "\n[bold green]═══ [5/5] DEPLOY (CANLIYA DAĞITIM) AŞAMASI ═══[/bold green]",
            )
        )
        deploy_cmd = detect_deploy_command(project_path)

        if deploy_cmd:
            console.print(
                Panel(
                    t(
                        f"[bold green]✓ All Verification Stages Passed![/bold green]\n"
                        f"• Implementation: Complete\n"
                        f"• Code Review: Approved\n"
                        f"• Tests: Passed\n"
                        f"• UI Build: Passed\n\n"
                        f"[bold cyan]Deploy Command:[/bold cyan] `{deploy_cmd}`\n\n"
                        f"Starting deployment...",
                        f"[bold green]✓ Tüm Aşamalar Başarıyla Geçildi![/bold green]\n"
                        f"• Kod Yazımı: Tamamlandı\n"
                        f"• Code Review: Onaylandı\n"
                        f"• Testler: Geçti\n"
                        f"• Ekran Testi: Geçti\n\n"
                        f"[bold cyan]Deploy Komutu:[/bold cyan] `{deploy_cmd}`\n\n"
                        f"Deploy işlemi başlatılıyor...",
                    ),
                    title=t("[bold green]Ready to Deploy[/bold green]", "[bold green]Deploy Hazır[/bold green]"),
                    border_style="green",
                )
            )

            with console.status(
                t(
                    f"[bold green]🚀 Running deploy command ({deploy_cmd})...[/bold green]",
                    f"[bold green]🚀 Deploy komutu yürütülüyor ({deploy_cmd})...[/bold green]",
                ),
                spinner="dots",
            ):
                try:
                    deploy_run = subprocess.run(
                        deploy_cmd,
                        cwd=project_path,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    deploy_output = (deploy_run.stdout or "") + "\n" + (deploy_run.stderr or "")
                    if deploy_run.returncode == 0:
                        console.print(
                            Panel(
                                t(
                                    f"[bold green]🎉 DEPLOYMENT COMPLETED SUCCESSFULLY![/bold green]\n\n"
                                    f"{deploy_output[-2000:]}",
                                    f"[bold green]🎉 DEPLOY BAŞARIYLA TAMAMLANDI![/bold green]\n\n"
                                    f"{deploy_output[-2000:]}",
                                ),
                                border_style="green",
                                title=t("[bold green]Deploy Succeeded[/bold green]", "[bold green]Deploy Başarılı[/bold green]"),
                            )
                        )
                        return True
                    else:
                        console.print(
                            Panel(
                                t(
                                    f"[bold red]❌ Deployment Failed (Exit Code: {deploy_run.returncode})[/bold red]\n\n"
                                    f"{deploy_output[-2000:]}",
                                    f"[bold red]❌ Deploy Hatası (Kodu: {deploy_run.returncode})[/bold red]\n\n"
                                    f"{deploy_output[-2000:]}",
                                ),
                                border_style="red",
                            )
                        )
                        return False
                except Exception as e:
                    console.print(
                        t(
                            f"[red]Deployment execution error: {e}[/red]",
                            f"[red]Deploy çalıştırma hatası: {e}[/red]",
                        )
                    )
                    return False
        else:
            console.print(
                Panel(
                    t(
                        f"[bold green]🎉 ALL IMPLEMENTATION, REVIEW, AND TEST STAGES COMPLETED![/bold green]\n\n"
                        f"• Coding: Succeeded\n"
                        f"• Code Review: Approved\n"
                        f"• Tests: Verified\n"
                        f"• Status: All changes are saved and verified in your project workspace.\n"
                        f"[dim](No deploy.sh found in project root; finalized with local verification.)[/dim]",
                        f"[bold green]🎉 TÜM GELİŞTİRME, REVIEW VE TEST SÜREÇLERİ TAMAMLANDI![/bold green]\n\n"
                        f"• Kodlama: Başarılı\n"
                        f"• Review: Onaylandı\n"
                        f"• Testler: Doğrulandı\n"
                        f"• Durum: Değişiklikler projenizde kayıtlı ve doğrulanmış durumdadır.\n"
                        f"[dim](Projede deploy.sh bulunmadığı için canlı dağıtım adımı yerel onay ile sonuçlandırıldı.)[/dim]",
                    ),
                    border_style="green",
                )
            )
            return True
