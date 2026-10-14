from typing import Optional
from agents.base_agent import BaseAgent
from config import AGENTS_META

class MuseAgent(BaseAgent):
    def __init__(self):
        super().__init__(AGENTS_META["muse"])

    def build_command(self, prompt: str, write_mode: bool = False) -> list[str]:
        return [
            self.bin_path,
            "exec",
            prompt
        ]

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> tuple[bool, str, Optional[str], bool]:
        combined = (stdout or "") + "\n" + (stderr or "")
        if "missing meta credentials" in combined.lower():
            return False, "", "Meta Muse kimlik doğrulama yapılmamış ('muse login' veya META_API_KEY gerekiyor).", True

        if returncode != 0 and not stdout.strip():
            return False, "", stderr.strip() or f"Muse hata kodu: {returncode}", False

        content = (stdout or "").strip()
        if not content:
            if stderr.strip():
                return False, "", stderr.strip(), False
            return False, "", "Muse boş yanıt döndürdü.", False

        return True, content, None, False
