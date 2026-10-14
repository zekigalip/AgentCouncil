from typing import Optional
from agents.base_agent import BaseAgent
from config import AGENTS_META

class ClaudeAgent(BaseAgent):
    def __init__(self):
        super().__init__(AGENTS_META["claude"])

    def build_command(self, prompt: str, write_mode: bool = False) -> list[str]:
        return [
            self.bin_path,
            "--dangerously-skip-permissions",
            "-p",
            prompt
        ]

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> tuple[bool, str, Optional[str], bool]:
        combined = (stdout or "") + "\n" + (stderr or "")
        
        # Oturum veya oran limiti kontrolü
        if "session limit" in combined.lower() or "rate limit" in combined.lower():
            # Reset saatini içeren mesajı yakala
            limit_msg = ""
            for line in combined.splitlines():
                if "session limit" in line.lower() or "resets" in line.lower():
                    limit_msg = line.strip()
                    break
            if not limit_msg:
                limit_msg = "Claude oturum limitine ulaşıldı."
            return False, "", limit_msg, True

        if returncode != 0 and not stdout.strip():
            error_msg = stderr.strip() or f"Claude beklenmedik hata koduyla çıktı: {returncode}"
            return False, "", error_msg, False

        content = stdout.strip()
        if not content and stderr.strip():
            return False, "", stderr.strip(), False

        return True, content, None, False
