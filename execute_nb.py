"""Script to execute and validate the demo notebook."""

from pathlib import Path
import nbformat
from nbclient import NotebookClient

NOTEBOOK_PATH = Path(__file__).resolve().parent / "notebook" / "flight_agent_demo.ipynb"


def execute_notebook():
    print(f"Reading notebook from {NOTEBOOK_PATH}...")
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    client = NotebookClient(nb, timeout=60, kernel_name="python3")
    print("Executing notebook cells...")
    executed_nb = client.execute()

    output_path = NOTEBOOK_PATH
    with open(output_path, "w", encoding="utf-8") as f:
        nbformat.write(executed_nb, f)

    print(f"✓ Notebook executed and saved successfully with full cell outputs to {output_path}!")


if __name__ == "__main__":
    execute_notebook()
