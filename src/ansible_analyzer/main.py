import argparse
import os
from pathlib import Path

from . import logger
from .graph import AnsibleGraph

DEFAULT_OUTPUT_PATH = Path(os.getcwd(), "ansible_graph.png")
DEFAULT_ROLES_DIR = Path(os.getcwd(), "roles")


def main():
    parser = argparse.ArgumentParser(prog="Ansible Analyzer")

    parser.add_argument(
        "-r",
        "--roles-dir",
        default=DEFAULT_ROLES_DIR,
        help="directory to load roles from",
    )
    parser.add_argument("-f", "--file-name", required=True, help="playbook path")
    parser.add_argument(
        "-o", "--output-path", default=DEFAULT_OUTPUT_PATH, help="playbook path"
    )

    args = parser.parse_args()

    g = AnsibleGraph(Path(args.roles_dir))
    fname = args.file_name
    output_path = Path(args.output_path)

    logger.info(f"Analyzing playbook {fname}")
    g.analyze_playbook(Path(fname))
    logger.info(f"Saving graph output to {output_path}")
    g.write_graph("png", output_path)
