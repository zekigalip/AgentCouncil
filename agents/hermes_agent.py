from typing import Optional
from agents.base_agent import BaseAgent
from config import AGENTS_META

class HermesAgent(BaseAgent):
    def __init__(self):
        super().__init__(AGENTS_META["hermes"])

    def build_command(self, prompt: str, write_mode: bool = False) -> list[str]:
        return [
            self.bin_path,
            "-z",
            prompt,
            "--yolo"
        ]

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> tuple[bool, str, Optional[str], bool]:
        combined = (stdout or "") + "\n" + (stderr or "")
        if "not logged in" in combined.lower() or "not configured" in combined.lower() or "select provider" in combined.lower():
            return False, "", "Hermes Agent için geçerli sağlayıcı/model seçilmemiş ('hermes setup' veya 'hermes model').", True

        if returncode != 0 and not stdout.strip():
            return False, "", stderr.strip() or f"Hermes hata kodu: {returncode}", False

        content = (stdout or "").strip()
        if not content:
            if stderr.strip():
                return False, "", stderr.strip(), False
            return False, "", "Hermes boş yanıt döndürdü.", False

        return True, content, None, False
