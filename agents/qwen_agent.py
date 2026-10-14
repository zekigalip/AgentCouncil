from typing import Optional
from agents.base_agent import BaseAgent
from config import AGENTS_META

class QwenAgent(BaseAgent):
    def __init__(self):
        super().__init__(AGENTS_META["qwen"])

    def build_command(self, prompt: str, write_mode: bool = False) -> list[str]:
        return [
            self.bin_path,
            "-p",
            prompt
        ]

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> tuple[bool, str, Optional[str], bool]:
        combined = (stdout or "") + "\n" + (stderr or "")
        if "no auth type" in combined.lower() or "not configured" in combined.lower():
            return False, "", "Alibaba Qwen-Code için kimlik doğrulama ayarlanmamış ('qwen auth' veya API anahtarı gerekiyor).", True

        if returncode != 0 and not stdout.strip():
            return False, "", stderr.strip() or f"Qwen hata kodu: {returncode}", False

        content = (stdout or "").strip()
        if not content:
            if stderr.strip():
                return False, "", stderr.strip(), False
            return False, "", "Qwen boş yanıt döndürdü.", False

        return True, content, None, False
