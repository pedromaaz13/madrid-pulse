"""Verifica el estado canónico y su correspondencia con la documentación."""

import re
import sys
from pathlib import Path

if __package__:
    from .governance_lib import REPO_ROOT, STATE_PATH, Record, has_text, load_state, records, repo_references, validate_state
    from .sync_docs import TASKS_DOC, sync
else:
    from governance_lib import REPO_ROOT, STATE_PATH, Record, has_text, load_state, records, repo_references, validate_state
    from sync_docs import TASKS_DOC, sync


def _verify_repo(root: Path, state: Record) -> list[str]:
    errors = []
    for location, field, path in dict.fromkeys(repo_references(state)):
        try:
            exists = (root / path).exists()
        except (OSError, ValueError):
            exists = False
        if not exists:
            errors.append(f"{location}: {field} apunta a una ruta inexistente: {path}")

    try:
        backlog = (root / TASKS_DOC).read_text(encoding="utf-8")
    except (OSError, ValueError) as error:
        errors.append(f"{TASKS_DOC}: {error}")
        return errors
    headings = set(re.findall(r"^## (\S+) — ", backlog, flags=re.MULTILINE))
    for task in records(state, "tasks"):
        task_id = task.get("id")
        if task.get("source") == TASKS_DOC and has_text(task_id) and task_id not in headings:
            errors.append(f"{task_id}: falta el encabezado «## {task_id} — » en {TASKS_DOC}")
    return errors


def check(root: Path) -> int:
    """Verifica el JSON, sus referencias y los bloques generados de una raíz."""
    try:
        state = load_state(root / STATE_PATH)
    except (OSError, ValueError) as error:
        print(f"{STATE_PATH}: {error}", file=sys.stderr)
        return 1

    errors = validate_state(state) + _verify_repo(root, state)
    for error in errors:
        print(error, file=sys.stderr)
    sync_status = sync(root, state, check=True)
    if sync_status == 1:
        print("GENERATED: bloques desincronizados; ejecuta python scripts/governance/sync_docs.py", file=sys.stderr)
    if errors or sync_status:
        return 1
    print("Documentación de gobernanza correcta.")
    return 0


if __name__ == "__main__":
    sys.exit(check(REPO_ROOT))
