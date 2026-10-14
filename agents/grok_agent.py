from typing import Optional
from agents.base_agent import BaseAgent
from config import AGENTS_META

class GrokAgent(BaseAgent):
    def __init__(self):
        super().__init__(AGENTS_META["grok"])

    def build_command(self, prompt: str, write_mode: bool = False) -> list[str]:
        perm = "bypassPermissions" if write_mode else "dontAsk"
        return [
            self.bin_path,
            "-p",
            prompt,
            "--permission-mode",
            perm
        ]

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> tuple[bool, str, Optional[str], bool]:
        combined = (stdout or "") + "\n" + (stderr or "")
        if "not signed in" in combined.lower():
            return False, "", "xAI Grok'a henüz giriş yapılmamış. 'grok login' komutuyla giriş yapabilirsiniz.", True

        if returncode != 0 and not stdout.strip():
            return False, "", stderr.strip() or f"Grok hata kodu: {returncode}", False

        content = (stdout or "").strip()
        if not content:
            if stderr.strip():
                return False, "", stderr.strip(), False
            return False, "", "Grok boş yanıt döndürdü.", False

        return True, content, None, False
