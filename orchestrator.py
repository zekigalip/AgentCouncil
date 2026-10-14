from typing import List, Dict, Any, Optional
from rich.console import Console
from agents import (
    AgentResponse,
    BaseAgent,
)
from ui import print_agent_response, print_summary_card
from role_manager import RoleConfig, get_agent_instances
from i18n import t

console = Console()


class MultiAgentOrchestrator:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = get_agent_instances()

    def run_discussion(
        self,
        project_name: str,
        project_path: str,
        user_prompt: str,
        role_config: Optional[RoleConfig] = None,
        previous_turns: Optional[List[Dict[str, Any]]] = None,
    ) -> List[AgentResponse]:
        """Execute a multi-agent council deliberation based on the configured roles."""
        cfg = role_config or RoleConfig()
        responses: List[AgentResponse] = []

        context_str = ""
        if previous_turns:
            context_str = t(
                "\n=== PREVIOUS ROUNDS & COUNCIL CONSENSUS ===\n",
                "\n=== ÖNCEKİ TURLAR VE VARILAN MUTABAKATLAR ===\n",
            )
            for idx, turn in enumerate(previous_turns, 1):
                context_str += t(
                    f"[Round {idx}] User Prompt: {turn.get('user_prompt', '')}\n",
                    f"[Tur {idx}] Kullanıcı Komutu: {turn.get('user_prompt', '')}\n",
                )
                for r in turn.get("responses", []):
                    if r.success and r.content:
                        summary_lines = [l for l in r.content.splitlines() if l.strip()]
                        brief = summary_lines[-1] if summary_lines else t("Completed", "Tamamlandı")
                        context_str += f"  • {r.name}: {brief}\n"
            context_str += "===============================================\n\n"

        # ==========================================
        # STAGE 1: ARCHITECT & ANALYST
        # ==========================================
        analyst = self.agents.get(cfg.analyst, self.agents["claude"])
        analyst_prompt = t(
            f"You are the Architect & System Analyst ({analyst.name}) on this project.\n"
            f"Project Name: {project_name}\n"
            f"Project Directory: {project_path}\n"
            f"{context_str}\n"
            f"The user gave the following task / instruction:\n"
            f"\"{user_prompt}\"\n\n"
            f"Please inspect the existing project files and structure to:\n"
            f"1. Perform a requirement analysis and assess the current state.\n"
            f"2. Identify key files and modules to modify, create, or inspect.\n"
            f"3. Provide a clear architectural roadmap for your council teammates: "
            f"Coder ({cfg.coder}), Reviewer ({cfg.reviewer}), Security ({cfg.security}), and Tester ({cfg.tester}).",
            f"Sen bu projedeki Mimarsın (Architect & Analyst - {analyst.name}).\n"
            f"Proje Adı: {project_name}\n"
            f"Proje Dizini: {project_path}\n"
            f"{context_str}\n"
            f"Kullanıcı şu komutu / görevi verdi:\n"
            f"\"{user_prompt}\"\n\n"
            f"Lütfen projenin mevcut dosyalarını ve durumunu inceleyerek:\n"
            f"1. İhtiyaç analizi ve mevcut durum tespitini yap.\n"
            f"2. Değiştirilmesi, eklenmesi veya incelenmesi gereken ana dosya ve modülleri belirle.\n"
            f"3. Ekip arkadaşların Coder ({cfg.coder}), Reviewer ({cfg.reviewer}), Security ({cfg.security}) ve Tester ({cfg.tester}) için mimari bir yol haritası sun.",
        )

        with console.status(
            t(
                f"[bold magenta]🟣 [1/5] {analyst.name} (Architect) is analyzing the codebase and drafting the roadmap...[/bold magenta]",
                f"[bold magenta]🟣 [1/5] {analyst.name} (Mimar) analizi ve mimari planı hazırlıyor...[/bold magenta]",
            ),
            spinner="dots",
        ):
            analyst_resp = analyst.execute(analyst_prompt, project_path)

        responses.append(analyst_resp)
        print_agent_response(analyst_resp)

        if analyst_resp.success and analyst_resp.content:
            analyst_section = f"=== ARCHITECTURAL ANALYSIS ({analyst.name}) ===\n{analyst_resp.content}\n"
        elif analyst_resp.is_limited:
            analyst_section = f"=== ARCHITECT ({analyst.name}) STATUS ===\n({analyst.name} rate/session limit active. Council continues with remaining members.)\n"
        else:
            analyst_section = f"=== ARCHITECT ({analyst.name}) STATUS ===\n({analyst.name} could not respond: {analyst_resp.error})\n"

        # ==========================================
        # STAGE 2: LEAD DEVELOPER & CODER
        # ==========================================
        coder = self.agents.get(cfg.coder, self.agents["codex"])
        coder_prompt = t(
            f"You are the Lead Developer & Coding Specialist ({coder.name}) on this project.\n"
            f"Project Name: {project_name}\n"
            f"Project Directory: {project_path}\n"
            f"{context_str}\n"
            f"User Task:\n"
            f"\"{user_prompt}\"\n\n"
            f"{analyst_section}\n"
            f"Please inspect the relevant project files and codebase to:\n"
            f"1. Evaluate the Architect's ({analyst.name}) analysis (points you agree with or refine).\n"
            f"2. Write concrete code blocks, function/class implementations, and exact changes needed.\n"
            f"3. Note any important technical details or package dependencies.",
            f"Sen bu projedeki Baş Geliştiricisin (Senior Developer & Coder - {coder.name}).\n"
            f"Proje Adı: {project_name}\n"
            f"Proje Dizini: {project_path}\n"
            f"{context_str}\n"
            f"Kullanıcının görevi:\n"
            f"\"{user_prompt}\"\n\n"
            f"{analyst_section}\n"
            f"Lütfen projedeki ilgili dosyaları ve kodu inceleyerek:\n"
            f"1. Mimarın ({analyst.name}) analizini değerlendir (katıldığın ve geliştirmek istediğin noktalar).\n"
            f"2. Gereken somut kod bloklarını, fonksiyon veya sınıf implementasyonlarını eksiksiz açıkla ve yaz.\n"
            f"3. Varsa dikkat edilmesi gereken teknik detayları ve paket bağımlılıklarını belirt.",
        )

        with console.status(
            t(
                f"[bold green]🟢 [2/5] {coder.name} (Coder) is inspecting the code and crafting concrete implementations...[/bold green]",
                f"[bold green]🟢 [2/5] {coder.name} (Coder) kodları inceliyor ve somut çözümü yazıyor...[/bold green]",
            ),
            spinner="dots",
        ):
            coder_resp = coder.execute(coder_prompt, project_path)

        responses.append(coder_resp)
        print_agent_response(coder_resp)

        if coder_resp.success and coder_resp.content:
            coder_section = f"=== CODING IMPLEMENTATION ({coder.name}) ===\n{coder_resp.content}\n"
        else:
            coder_section = f"=== CODER ({coder.name}) STATUS ===\n({coder.name} could not respond: {coder_resp.error})\n"

        # ==========================================
        # STAGE 3: SENIOR CODE REVIEWER
        # ==========================================
        reviewer = self.agents.get(cfg.reviewer, self.agents["cursor"])
        reviewer_prompt = t(
            f"You are the Senior Code Reviewer & Optimization Specialist ({reviewer.name}) on this project.\n"
            f"Project Name: {project_name}\n"
            f"Project Directory: {project_path}\n"
            f"{context_str}\n"
            f"User Task:\n"
            f"\"{user_prompt}\"\n\n"
            f"{analyst_section}\n"
            f"{coder_section}\n"
            f"Please inspect the project files and the Coder's ({coder.name}) proposed solution to:\n"
            f"1. Review code quality, performance, clean code practices, and refactoring opportunities.\n"
            f"2. Point out any missed functional details or practical improvements.",
            f"Sen bu projedeki Kıdemli Kod İnceleyici ve Optimizasyon Uzmanısın (Reviewer - {reviewer.name}).\n"
            f"Proje Adı: {project_name}\n"
            f"Proje Dizini: {project_path}\n"
            f"{context_str}\n"
            f"Kullanıcının görevi:\n"
            f"\"{user_prompt}\"\n\n"
            f"{analyst_section}\n"
            f"{coder_section}\n"
            f"Lütfen projedeki kodları ve Coder'ın ({coder.name}) sunduğu çözümü inceleyerek:\n"
            f"1. Kod önerilerini gözden geçir; performans, temiz kod (clean code) ve refactoring önerilerini belirt.\n"
            f"2. Varsa gözden kaçan fonksiyonel detayları veya pratik iyileştirmeleri sun.",
        )

        with console.status(
            t(
                f"[bold cyan]🔵 [3/5] {reviewer.name} (Reviewer) is performing code review and optimization analysis...[/bold cyan]",
                f"[bold cyan]🔵 [3/5] {reviewer.name} (Reviewer) kod incelemesini ve optimizasyon önerilerini hazırlıyor...[/bold cyan]",
            ),
            spinner="dots",
        ):
            reviewer_resp = reviewer.execute(reviewer_prompt, project_path)

        responses.append(reviewer_resp)
        print_agent_response(reviewer_resp)

        if reviewer_resp.success and reviewer_resp.content:
            reviewer_section = f"=== CODE REVIEW & OPTIMIZATION ({reviewer.name}) ===\n{reviewer_resp.content}\n"
        elif reviewer_resp.is_limited:
            reviewer_section = f"=== REVIEWER ({reviewer.name}) STATUS ===\n({reviewer.name} awaiting auth/limit. Council continues.)\n"
        else:
            reviewer_section = f"=== REVIEWER ({reviewer.name}) STATUS ===\n({reviewer.name} could not respond: {reviewer_resp.error})\n"

        # ==========================================
        # STAGE 4: SECURITY & EDGE-CASE ANALYST
        # ==========================================
        security = self.agents.get(cfg.security, self.agents["grok"])
        security_prompt = t(
            f"You are the Security, Fault-Tolerance & Edge-Case Analyst ({security.name}) on this project.\n"
            f"Project Name: {project_name}\n"
            f"Project Directory: {project_path}\n"
            f"{context_str}\n"
            f"User Task:\n"
            f"\"{user_prompt}\"\n\n"
            f"{analyst_section}\n"
            f"{coder_section}\n"
            f"{reviewer_section}\n"
            f"Please inspect the project and your teammates' architectural/coding proposals to:\n"
            f"1. Audit for security vulnerabilities, authorization flaws, and data leakage risks.\n"
            f"2. Analyze critical edge cases, exception handling, network/timeout failures, and unexpected inputs.\n"
            f"3. Specify concrete defensive mechanisms to harden fragile points in the code.",
            f"Sen bu projedeki Güvenlik, Hata Toleransı ve Uç Durum Analistisin ({security.name}).\n"
            f"Proje Adı: {project_name}\n"
            f"Proje Dizini: {project_path}\n"
            f"{context_str}\n"
            f"Kullanıcının görevi:\n"
            f"\"{user_prompt}\"\n\n"
            f"{analyst_section}\n"
            f"{coder_section}\n"
            f"{reviewer_section}\n"
            f"Lütfen projeyi ve ekip arkadaşlarının sunduğu mimari/kodlama çözümlerini inceleyerek:\n"
            f"1. Güvenlik açıkları, yetkilendirme sorunları ve veri sızıntısı risklerini denetle.\n"
            f"2. Kritik uç durumları (edge cases), exception handling, ağ/timeout ve beklenmedik girdileri analiz et.\n"
            f"3. Kodun kırılgan noktalarını güçlendirecek net savunma mekanizmalarını belirt.",
        )

        with console.status(
            t(
                f"[bold red]🔴 [4/5] {security.name} (Security) is auditing security vulnerabilities and edge cases...[/bold red]",
                f"[bold red]🔴 [4/5] {security.name} (Güvenlik) uç durum ve güvenlik denetimini gerçekleştiriyor...[/bold red]",
            ),
            spinner="dots",
        ):
            security_resp = security.execute(security_prompt, project_path)

        responses.append(security_resp)
        print_agent_response(security_resp)

        if security_resp.success and security_resp.content:
            security_section = f"=== SECURITY & EDGE-CASE AUDIT ({security.name}) ===\n{security_resp.content}\n"
        else:
            security_section = f"=== SECURITY ({security.name}) STATUS ===\n({security.name} could not respond: {security_resp.error})\n"

        # ==========================================
        # STAGE 5: QA & SYNTHESIS LEAD
        # ==========================================
        tester = self.agents.get(cfg.tester, self.agents["agy"])
        tester_prompt = t(
            f"You are the Principal Engineer, QA & Synthesis Lead ({tester.name}) on this project.\n"
            f"Project Name: {project_name}\n"
            f"Project Directory: {project_path}\n"
            f"{context_str}\n"
            f"User Task:\n"
            f"\"{user_prompt}\"\n\n"
            f"{analyst_section}\n"
            f"{coder_section}\n"
            f"{reviewer_section}\n"
            f"{security_section}\n"
            f"Please evaluate all council members' proposals and the project codebase to:\n"
            f"1. Define test scenarios, unit/integration tests, and verification criteria.\n"
            f"2. Establish council consensus (resolve any trade-offs or conflicts).\n"
            f"3. Present a clear, bulleted final consensus summary and step-by-step execution plan.",
            f"Sen bu projedeki Baş Mühendis ve Test Liderisin ({tester.name}).\n"
            f"Proje Adı: {project_name}\n"
            f"Proje Dizini: {project_path}\n"
            f"{context_str}\n"
            f"Kullanıcının görevi:\n"
            f"\"{user_prompt}\"\n\n"
            f"{analyst_section}\n"
            f"{coder_section}\n"
            f"{reviewer_section}\n"
            f"{security_section}\n"
            f"Lütfen tüm ekip arkadaşlarının sunduğu yaklaşımları ve projenin kod tabanını değerlendirerek:\n"
            f"1. Test senaryolarını, birim/entegrasyon testlerini ve performans gereksinimlerini belirle.\n"
            f"2. Ekip arasındaki mutabakatı sağla (varsa çelişkileri çöz).\n"
            f"3. Kullanıcı için net, maddeler halinde nihai bir konsensüs özeti ve uygulanacak adım adım eylem planı sun.",
        )

        with console.status(
            t(
                f"[bold yellow]🟡 [5/5] {tester.name} (QA & Synthesis Lead) is finalizing the test strategy and consensus plan...[/bold yellow]",
                f"[bold yellow]🟡 [5/5] {tester.name} (Test Lideri) test ve nihai konsensüs raporunu tamamlıyor...[/bold yellow]",
            ),
            spinner="dots",
        ):
            tester_resp = tester.execute(tester_prompt, project_path)

        responses.append(tester_resp)
        print_agent_response(tester_resp)

        print_summary_card(responses)

        return responses
