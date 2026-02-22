import os
from pathlib import Path

from . import logger


class RoleStats:
    name: str
    path: Path
    total_tasks: set[str]
    used_tasks: set[str]

    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.total_tasks = set()
        self.used_tasks = set()

    def load_tasks(self):
        self.total_tasks = set(os.listdir(self.path / "tasks"))

        if not self.total_tasks:
            logger.warning(f"role {self.name} doesn't contain any task files!")
