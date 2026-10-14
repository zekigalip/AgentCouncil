from typing import Optional
from agents.base_agent import BaseAgent
from config import AGENTS_META

class CodexAgent(BaseAgent):
    def __init__(self):
        super().__init__(AGENTS_META["codex"])

    def build_command(self, prompt: str, write_mode: bool = False) -> list[str]:
        cmd = [self.bin_path, "exec", "--skip-git-repo-check"]
        if write_mode:
            cmd.extend(["--sandbox", "workspace-write"])
        cmd.append(prompt)
        return cmd

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> tuple[bool, str, Optional[str], bool]:
        if returncode != 0 and not stdout.strip():
            return False, "", stderr.strip() or f"Codex hata kodu ile sonlandı: {returncode}", False

        raw = stdout or ""
        # Codex çıktısını ayıkla: "codex\n" bloğundan sonrasını al
        idx = raw.find("\ncodex\n")
        if idx != -1:
            clean_text = raw[idx + len("\ncodex\n"):]
        else:
            # Yedek ayıklama: Başlıktaki sistem loglarını temizle
            lines = raw.splitlines()
            filtered = []
            for line in lines:
                if any(line.startswith(prefix) for prefix in [
                    "202", "OpenAI Codex", "--------", "workdir:", "model:",
                    "provider:", "approval:", "sandbox:", "reasoning ", "session id:"
                ]):
                    continue
                filtered.append(line)
            clean_text = "\n".join(filtered)

        # Sondaki token sayımını ayıkla
        tokens_idx = clean_text.rfind("\ntokens used")
        if tokens_idx != -1:
            clean_text = clean_text[:tokens_idx]

        clean_text = clean_text.strip()
        if not clean_text:
            if stderr.strip():
                return False, "", stderr.strip(), False
            return False, "", "Codex boş yanıt döndürdü.", False

        return True, clean_text, None, False
