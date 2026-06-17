"""mempalace Brain: the default production backend.

Wraps the public `mempalace` CLI (pip install mempalace). The palace lives outside the git tree at the
configured path; the persona's knowledge goes into its own wing, isolated from any other palace.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .base import Brain, Hit

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


class MempalaceBrain(Brain):
    def __init__(self, palace_path: str, wing: str, search_results: int = 6,
                 agent: str = "MaskPersona AI") -> None:
        self.palace = str(Path(palace_path).expanduser())
        self.wing = wing
        self.search_results = search_results
        self.agent = agent

    def _run(self, *args: str, timeout: int = 120) -> str:
        cmd = ["mempalace", "--palace", self.palace, *args]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if out.returncode != 0:
            raise RuntimeError(f"mempalace failed: {' '.join(cmd)}\n{out.stderr.strip()}")
        return _ANSI.sub("", out.stdout)

    def init(self) -> None:
        Path(self.palace).expanduser().mkdir(parents=True, exist_ok=True)
        # mempalace creates its index lazily on first mine; status confirms it is reachable.
        self._run("status")

    def mine(self, knowledge_dir: str | Path) -> int:
        out = self._run("mine", "--wing", self.wing, "--no-gitignore",
                        "--agent", self.agent, str(knowledge_dir))
        m = re.search(r"(\d+)\s+drawers", out)
        return int(m.group(1)) if m else 0

    def search(self, query: str, k: int | None = None) -> list[Hit]:
        k = k or self.search_results
        out = self._run("search", query, "--results", str(k))
        hits: list[Hit] = []
        for i, block in enumerate(b.strip() for b in out.split("\n\n") if b.strip()):
            hits.append(Hit(text=block, source="mempalace", score=float(k - i)))
        return hits[:k]

    def sync(self) -> None:
        self._run("sync", "--apply", "--wing", self.wing)

    def status(self) -> dict:
        out = self._run("status")
        m = re.search(r"(\d+)\s+drawers", out)
        return {"backend": "mempalace", "wing": self.wing, "palace": self.palace,
                "items": int(m.group(1)) if m else 0}
