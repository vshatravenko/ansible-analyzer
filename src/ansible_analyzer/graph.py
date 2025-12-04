import logging
from pathlib import Path

import pydot
from yaml import safe_load

PLAYBOOK_COLOR = "azure"
PLAYBOOK_SHAPE = "ellipse"
TASK_COLOR = "aliceblue"
TASK_SHAPE = "rectangle"

NODE_MARGIN = 0.5
NODE_STYLE = "filled"

PLAYBOOK_KEYWORDS = ["deployment_task"]
ROLE_KEYWORDS = ["include_tasks"]


logger = logging.getLogger("ansible-analyzer")


def parse_yaml(path: Path):
    with open(path, "r") as f:
        return safe_load(f)


def load_playbook(path: Path) -> list[dict]:
    return parse_yaml(path)


class AnsibleGraph:
    def __init__(self, roles_dir: Path) -> None:
        self.roles_dir = Path(roles_dir)
        self.graph = pydot.Dot(strict=True)

    def analyze_playbook(self, path: Path):
        """
        Goes through each play in the input playbook file,
        looks for roles, tasks, and other plays being invoked
        """

        plays = load_playbook(path)
        id = f"playbook/{path.parts[-1]}"

        logger.info(f"created root node {id}")
        root = pydot.Node(
            id,
            label=id,
            shape=PLAYBOOK_SHAPE,
            fillcolor=PLAYBOOK_COLOR,
            margin=NODE_MARGIN,
            style=NODE_STYLE,
        )
        self.graph.add_node(root)

        for i, play in enumerate(plays):
            name = play["name"] if "name" in play.keys() else str(i)
            logger.info(f"analyzing play: {name}")

            if "roles" in play.keys():
                # TODO: support multiple roles
                role_name = play.get("roles", [])[0]

                play_vars = play.get("vars", {})
                self.analyze_role(root, role_name, play_vars)

    def analyze_role(self, parent: pydot.Node, name: str, play_vars: dict = {}):
        """
        Starts from tasks/main.yml and analyzes each task
        including its invocations
        """
        logger.info(f"analyze_role for {name} started")
        if play_vars:
            logger.info(f"included vars: {play_vars}")

        role_dir = self.roles_dir.joinpath(name)
        base_dir = role_dir / "tasks"

        if not base_dir.exists():
            raise ValueError(f"{base_dir} not found")

        root = self.analyze_task_file(name, base_dir, "main.yml", play_vars)
        self.graph.add_node(root)
        self.graph.add_edge(pydot.Edge(parent, root))

    # Need to analyze blocks too
    def analyze_task_file(
        self, role_name: str, base_path: Path, task_file: str, play_vars: dict = {}
    ) -> pydot.Node:
        path = base_path / task_file
        logger.info(f"Analyzing {path} task file")

        tasks = parse_yaml(path)
        basename = path.parts[-1]

        root = pydot.Node(
            f"role/{role_name}/{basename}",
            label=f"role/{role_name}/{task_file}",
            shape=TASK_SHAPE,
            fillcolor=TASK_COLOR,
            margin=NODE_MARGIN,
            style=NODE_STYLE,
        )

        for task in list(tasks):
            if "block" in task.keys():
                self.parse_block(task.get("block", {}))

            INCLUDE_TASK_KEY = "ansible.builtin.include_tasks"
            if INCLUDE_TASK_KEY in task.keys():
                logger.info(f"include_tasks detected in {basename}")
                include_path = task.get(INCLUDE_TASK_KEY, "")

                if "{{" in include_path:
                    logger.info(f"dynamic include_tasks detected: {include_path}")
                    include_path_var = include_path.split(" ")[1]
                    include_path = play_vars.get(include_path_var)
                    if not include_path:
                        raise ValueError(
                            f"{include_path_var} is missing from play vars - {play_vars}"
                        )

                node = self.analyze_task_file(
                    role_name, base_path, include_path, play_vars
                )

                self.graph.add_node(node)
                self.graph.add_edge(pydot.Edge(root, node))

        return root

    def parse_block(self, block: dict):
        pass

    def write_graph(self, format: str, output_path: Path):
        logger.info(f"Writing graph output in {format} format to {output_path}")
        self.graph.write(path=str(output_path), format=format)
