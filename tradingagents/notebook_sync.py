"""Google NotebookLM sync via the ``nlm`` CLI tool.

Uploads the daily digest file to a NotebookLM notebook, replacing the
previous version if one exists.  Entirely opt-in: if no ``NOTEBOOK_ID``
is configured the function is a silent no-op.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from rich.console import Console

console = Console()


def sync_to_notebooklm(digest_path: Path, notebook_id: str | None = None) -> None:
    """Upload *digest_path* to Google NotebookLM.

    Parameters
    ----------
    digest_path:
        Path to the digest markdown file to upload.
    notebook_id:
        NotebookLM notebook ID.  Falls back to the ``NOTEBOOK_ID``
        environment variable when *None*.
    """
    if notebook_id is None:
        notebook_id = os.environ.get("NOTEBOOK_ID")
    if not notebook_id:
        return  # opt-in — silently skip when not configured

    filename = digest_path.name

    # Delete previous version of this source (if any)
    try:
        list_result = subprocess.run(
            ["nlm", "source", "list", notebook_id],
            capture_output=True,
            text=True,
        )
        if list_result.returncode == 0:
            for line in list_result.stdout.splitlines():
                if filename in line:
                    # Expected format: "<source_id>  <filename>  ..."
                    source_id = line.split()[0].strip()
                    subprocess.run(
                        ["nlm", "source", "delete", notebook_id, source_id],
                        capture_output=True,
                        text=True,
                    )
                    console.print(f"[dim]Removed old digest source {source_id}[/dim]")
                    break
    except (FileNotFoundError, OSError) as exc:
        console.print(f"[yellow]Warning: could not list nlm sources: {exc}[/yellow]")
        return

    # Upload the new version
    try:
        add_result = subprocess.run(
            ["nlm", "source", "add", notebook_id, "--file", str(digest_path)],
            capture_output=True,
            text=True,
        )
        if add_result.returncode == 0:
            console.print(f"[green]Synced digest to NotebookLM notebook {notebook_id}[/green]")
        else:
            console.print(
                f"[yellow]Warning: nlm upload exited {add_result.returncode}: "
                f"{add_result.stderr.strip()}[/yellow]"
            )
    except (FileNotFoundError, OSError) as exc:
        console.print(f"[yellow]Warning: could not upload to NotebookLM: {exc}[/yellow]")
