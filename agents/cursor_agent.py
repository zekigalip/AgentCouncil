import shutil
from typing import Optional
from agents.base_agent import BaseAgent
from config import AGENTS_META

class CursorAgent(BaseAgent):
    def __init__(self):
        super().__init__(AGENTS_META["cursor"])

    def build_command(self, prompt: str, write_mode: bool = False) -> list[str]:
        cmd = [self.bin_path, "--trust"]
        if write_mode:
            cmd.append("--force")
        cmd.extend(["-p", prompt])
        return cmd

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> tuple[bool, str, Optional[str], bool]:
        combined = (stdout or "") + "\n" + (stderr or "")

        # Kimlik doğrulama / oturum süresi dolması kontrolü
        if "authentication required" in combined.lower() or "run 'agent login'" in combined.lower():
            auth_msg = (
                "Cursor Agent oturum süresi dolmuş veya kimlik doğrulaması gerekiyor.\n"
                "Çözüm: Terminalde 'cursor-agent login' (veya 'agent login') çalıştırarak oturumu yenileyin, "
                "ya da CURSOR_API_KEY ortam değişkenini tanımlayın."
            )
            return False, "", auth_msg, True

        if returncode != 0 and not stdout.strip():
            error_msg = stderr.strip() or f"Cursor Agent hata kodu ile sonlandı: {returncode}"
            return False, "", error_msg, False

        content = (stdout or "").strip()
        if not content:
            if stderr.strip():
                return False, "", stderr.strip(), False
            return False, "", "Cursor Agent boş yanıt döndürdü.", False

        return True, content, None, False
