from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import subprocess
import time
from config import TIMEOUT_SECONDS

class AgentResponse:
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        success: bool,
        content: str,
        execution_time: float = 0.0,
        error: Optional[str] = None,
        is_limited: bool = False
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.success = success
        self.content = content
        self.execution_time = execution_time
        self.error = error
        self.is_limited = is_limited

class BaseAgent(ABC):
    def __init__(self, meta: Dict[str, Any]):
        self.id = meta["id"]
        self.name = meta["name"]
        self.provider = meta["provider"]
        self.role = meta["role"]
        self.icon = meta["icon"]
        self.style = meta["style"]
        self.border_style = meta["border_style"]
        self.bin_path = meta["bin"]

    @abstractmethod
    def build_command(self, prompt: str, write_mode: bool = False) -> list[str]:
        """Ajan için çalıştırılacak komut listesini döndürür."""
        pass

    @abstractmethod
    def parse_output(self, stdout: str, stderr: str, returncode: int) -> tuple[bool, str, Optional[str], bool]:
        """Çıktıyı ayrıştırır. Döndürür: (success, content, error, is_limited)"""
        pass

    def execute(
        self,
        prompt: str,
        project_dir: str,
        timeout: int = TIMEOUT_SECONDS,
        write_mode: bool = False
    ) -> AgentResponse:
        """Belirtilen proje dizininde ajanı çalıştırır ve çıktısını döndürür."""
        cmd = self.build_command(prompt, write_mode=write_mode)
        start_time = time.time()
        
        try:
            process = subprocess.run(
                cmd,
                cwd=project_dir,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = time.time() - start_time
            success, content, error, is_limited = self.parse_output(
                process.stdout, process.stderr, process.returncode
            )
            return AgentResponse(
                agent_id=self.id,
                name=self.name,
                role=self.role,
                success=success,
                content=content,
                execution_time=elapsed,
                error=error,
                is_limited=is_limited
            )
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            return AgentResponse(
                agent_id=self.id,
                name=self.name,
                role=self.role,
                success=False,
                content="",
                execution_time=elapsed,
                error=f"Zaman aşımı ({timeout}s). Ajan yanıt vermedi.",
                is_limited=False
            )
        except Exception as e:
            elapsed = time.time() - start_time
            return AgentResponse(
                agent_id=self.id,
                name=self.name,
                role=self.role,
                success=False,
                content="",
                execution_time=elapsed,
                error=str(e),
                is_limited=False
            )
