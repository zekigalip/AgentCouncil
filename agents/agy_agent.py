from typing import Optional
from agents.base_agent import BaseAgent
from config import AGENTS_META

class AgyAgent(BaseAgent):
    def __init__(self):
        super().__init__(AGENTS_META["agy"])

    def build_command(self, prompt: str, write_mode: bool = False) -> list[str]:
        cmd = [self.bin_path]
        if write_mode:
            cmd.extend(["--dangerously-skip-permissions", "--mode", "accept-edits"])
        cmd.extend(["-p", prompt])
        return cmd

    def parse_output(self, stdout: str, stderr: str, returncode: int) -> tuple[bool, str, Optional[str], bool]:
        if returncode != 0 and not stdout.strip():
            return False, "", stderr.strip() or f"Agy hata kodu ile sonlandı: {returncode}", False

        clean_text = (stdout or "").strip()
        if not clean_text:
            if stderr.strip():
                return False, "", stderr.strip(), False
            return False, "", "Agy boş yanıt döndürdü.", False

        return True, clean_text, None, False
