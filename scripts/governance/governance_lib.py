"""Carga y validación del estado canónico de Madrid Pulse."""

import json
import re
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

type Record = dict[str, Any]

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = Path("docs/governance/PROJECT_STATE.json")
STATUS_FIELDS = (
    "implementation_status",
    "review_status",
    "integration_status",
    "deployment_status",
)
COLLECTIONS = {
    "tasks": STATUS_FIELDS,
    "milestones": (*STATUS_FIELDS, "closure"),
    "phases": ("implementation_status", "closure"),
    "proposed_extensions": (),
    "human_gates": ("status",),
    "open_findings": (),
}
REPO_PREFIXES = ("docs/", "scripts/", "tests/", "apps/", "packages/", "services/", "infra/")
REFERENCE_FIELDS = ("evidence", "gate_evidence", "source", "deployment_evidence")
IMPLEMENTED = ("IMPLEMENTED", "IMPLEMENTED_WITH_OPEN_GATE")
UNSTARTED = ("PLANNED", "NOT_STARTED")


def _invalid_constant(value: str) -> None:
    raise ValueError(f"constante JSON inválida: {value}")


def load_state(path: Path) -> Record:
    """Lee un objeto JSON en UTF-8."""
    state = json.loads(path.read_text(encoding="utf-8"), parse_constant=_invalid_constant)
    if not isinstance(state, dict):
        raise ValueError("la raíz JSON debe ser un objeto")
    return state


def has_text(value: object) -> bool:
    """Indica si el valor es un texto no vacío."""
    return isinstance(value, str) and bool(value.strip())


def text_entries(value: object) -> list[str]:
    """Devuelve las entradas de texto de un campo escalar o de una lista."""
    if isinstance(value, str):
        return [value] if has_text(value) else []
    if isinstance(value, list):
        return [entry for entry in value if has_text(entry)]
    return []


def records(state: Record, collection: str) -> Iterator[Record]:
    """Itera los objetos de una colección, incluso durante la validación."""
    value = state.get(collection)
    if isinstance(value, list):
        yield from (item for item in value if isinstance(item, dict))


def is_repo_path(value: str) -> bool:
    """Identifica referencias con prefijo de ruta del repositorio."""
    return value.startswith(REPO_PREFIXES)


def reference_entries(record: Record, field: str) -> list[str]:
    """Lee referencias, incluidas las evidencias textuales de las fases."""
    value = record.get(field)
    if field == "gate_evidence" and isinstance(value, str):
        return [entry.strip() for entry in value.split(";") if has_text(entry)]
    return text_entries(value)


def _sha(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", value))


def _date(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _entry_id(record: Record, fallback: str) -> str:
    value = record.get("id")
    return value if has_text(value) else fallback


def _check_formats(record: Record, location: str) -> Iterator[str]:
    for field, value in record.items():
        if value == "UNKNOWN":
            continue
        if field in ("head", "origin_main", "product_baseline_head") or (
            value is not None and (field == "sha" or field.endswith(("_sha", "_head")))
        ):
            if not _sha(value):
                yield f"{location}: {field} debe ser hexadecimal de 7–40 caracteres o UNKNOWN"
        if value is not None and (field == "date" or field.endswith("_date")):
            if not _date(value):
                yield f"{location}: {field} debe ser una fecha ISO YYYY-MM-DD o UNKNOWN"


def _check_gate(record: Record, location: str, gate_field: str) -> Iterator[str]:
    if record.get("closure") == "CLOSED":
        if not has_text(record.get(gate_field)):
            yield f"{location}: CLOSED exige {gate_field}"
        if not reference_entries(record, "gate_evidence"):
            yield f"{location}: CLOSED exige gate_evidence"


def _check_task(task: Record, location: str) -> Iterator[str]:
    implementation = task.get("implementation_status")
    review = task.get("review_status")
    integration = task.get("integration_status")
    evidence = task.get("evidence")
    has_evidence = isinstance(evidence, list) and bool(text_entries(evidence))
    if review == "APPROVED" or implementation in IMPLEMENTED:
        if not has_text(task.get("reviewer")):
            yield f"{location}: {review if review == 'APPROVED' else implementation} exige reviewer"
        if not has_evidence:
            yield f"{location}: {review if review == 'APPROVED' else implementation} exige evidence"
    if review == "APPROVED" and has_text(task.get("reviewer")):
        if task["reviewer"].strip().casefold() == str(task.get("executor", "")).strip().casefold():
            yield f"{location}: APPROVED exige reviewer distinto de executor"
    if implementation in IMPLEMENTED and not has_text(task.get("executor")):
        yield f"{location}: {implementation} exige executor"
    if implementation in UNSTARTED:
        if review == "APPROVED":
            yield f"{location}: {implementation} es incompatible con APPROVED"
        if integration == "MERGED":
            yield f"{location}: {implementation} es incompatible con MERGED"
    if integration == "MERGED" and not _sha(task.get("merge_sha")):
        yield f"{location}: MERGED exige merge_sha hexadecimal de 7–40 caracteres"


def _check_links(
    record: Record, location: str, field: str, tasks: dict[str, Record]
) -> Iterator[str]:
    values = record.get(field)
    if not isinstance(values, list):
        yield f"{location}: {field} debe ser una lista de IDs de tarea"
        return
    for value in values:
        if not isinstance(value, str) or value not in tasks:
            yield f"{location}: {field} referencia una tarea inexistente: {value!r}"


def _cycles(tasks: dict[str, Record]) -> Iterator[str]:
    visited: set[str] = set()
    for task_id in tasks:
        if task_id in visited:
            continue
        visited.add(task_id)
        active = {task_id: 0}
        stack = [(task_id, iter(text_entries(tasks[task_id].get("depends_on"))))]
        while stack:
            current, dependencies = stack[-1]
            dependency = next(dependencies, None)
            if dependency is None:
                del active[current]
                stack.pop()
            elif dependency in active:
                cycle = [item for item, _ in stack[active[dependency]:]]
                yield f"{current}: ciclo en depends_on: {' → '.join([*cycle, dependency])}"
            elif dependency in tasks and dependency not in visited:
                visited.add(dependency)
                active[dependency] = len(stack)
                stack.append((dependency, iter(text_entries(tasks[dependency].get("depends_on")))))


def validate_state(state: Record) -> list[str]:
    """Devuelve los errores de esquema y coherencia sin acceder al repositorio."""
    errors: list[str] = []
    if type(state.get("schema_version")) is not int or state["schema_version"] != 1:
        errors.append("PROJECT_STATE: schema_version debe ser 1")
    for field in ("as_of", "product_verdict", "vocab"):
        if not isinstance(state.get(field), dict):
            errors.append(f"PROJECT_STATE: {field} debe ser un objeto")
    vocab = state.get("vocab")
    if not isinstance(vocab, dict):
        vocab = {}
    for field in (*STATUS_FIELDS, "closure", "human_gate_status"):
        values = vocab.get(field)
        if not isinstance(values, list) or not values or not all(map(has_text, values)):
            errors.append(f"PROJECT_STATE: vocab.{field} debe ser una lista de estados")

    tasks: dict[str, Record] = {}
    ids: dict[str, str] = {}
    verdict = state.get("product_verdict")
    no_go = isinstance(verdict, dict) and verdict.get("public_deployment") == "NO-GO"
    public_gate = any(
        gate.get("id") == "HG-LIVE-PUBLIC" and gate.get("status") == "APPROVED_BY_OWNER"
        for gate in records(state, "human_gates")
    )
    as_of = state.get("as_of")
    if isinstance(as_of, dict):
        errors.extend(_check_formats(as_of, "as_of"))

    for collection, fields in COLLECTIONS.items():
        items = state.get(collection)
        if not isinstance(items, list):
            errors.append(f"PROJECT_STATE: {collection} debe ser una lista")
            continue
        for index, record in enumerate(items):
            label = f"{collection}[{index}]"
            if not isinstance(record, dict):
                errors.append(f"{label}: debe ser un objeto")
                continue
            location = _entry_id(record, label)
            if not has_text(record.get("id")):
                errors.append(f"{label}: id debe ser un texto no vacío")
            elif location in ids:
                errors.append(f"{location}: ID duplicado en {ids[location]} y {collection}")
            else:
                ids[location] = collection
            for field in fields:
                vocab_field = "human_gate_status" if field == "status" else field
                if record.get(field) not in text_entries(vocab.get(vocab_field)):
                    errors.append(f"{location}: {field} fuera de vocab: {record.get(field)!r}")
            errors.extend(_check_formats(record, location))

            if collection == "tasks":
                tasks.setdefault(location, record)
                errors.extend(_check_task(record, location))
            elif collection == "milestones":
                errors.extend(_check_gate(record, location, "gate"))
                merge = record.get("merge")
                if merge is not None and not isinstance(merge, dict):
                    errors.append(f"{location}: merge debe ser un objeto")
                if isinstance(merge, dict):
                    errors.extend(_check_formats(merge, f"{location} (merge)"))
                if record.get("integration_status") == "MERGED":
                    if not isinstance(merge, dict) or not _sha(merge.get("sha")):
                        errors.append(f"{location}: MERGED exige merge.sha hexadecimal de 7–40 caracteres")
            elif collection == "phases":
                errors.extend(_check_gate(record, location, "exit_gate"))
                if record.get("closure") == "CLOSED" and record.get("implementation_status") == "IMPLEMENTED_WITH_OPEN_GATE":
                    errors.append(f"{location}: CLOSED es incompatible con IMPLEMENTED_WITH_OPEN_GATE")
            elif collection == "human_gates" and record.get("status") == "APPROVED_BY_OWNER":
                if record.get("approved_by") != "owner":
                    errors.append(f"{location}: APPROVED_BY_OWNER exige approved_by = owner")
                if not _date(record.get("date")):
                    errors.append(f"{location}: APPROVED_BY_OWNER exige date ISO YYYY-MM-DD")
                if not text_entries(record.get("evidence")):
                    errors.append(f"{location}: APPROVED_BY_OWNER exige evidence")

            if collection in ("tasks", "milestones"):
                deployment = record.get("deployment_status")
                if has_text(deployment) and deployment not in ("NOT_DEPLOYED", "NOT_APPLICABLE") and not text_entries(record.get("deployment_evidence")):
                    errors.append(f"{location}: {deployment} exige deployment_evidence")
                if deployment == "PUBLIC":
                    if not public_gate:
                        errors.append(f"{location}: PUBLIC exige HG-LIVE-PUBLIC en APPROVED_BY_OWNER")
                    if no_go:
                        errors.append(f"{location}: PUBLIC es incompatible con el veredicto NO-GO")

    for task in records(state, "tasks"):
        errors.extend(_check_links(task, _entry_id(task, "tasks"), "depends_on", tasks))
    for collection in ("milestones", "phases"):
        for record in records(state, collection):
            location = _entry_id(record, collection)
            errors.extend(_check_links(record, location, "tasks", tasks))
            if collection == "milestones" and record.get("closure") == "CLOSED":
                for task_id in text_entries(record.get("tasks")):
                    status = tasks.get(task_id, {}).get("implementation_status")
                    if status in (*UNSTARTED, "IN_PROGRESS", "BLOCKED"):
                        errors.append(f"{location}: CLOSED contiene {task_id} en {status}")
    errors.extend(_cycles(tasks))
    return errors


def repo_references(state: Record) -> Iterator[tuple[str, str, str]]:
    """Devuelve el ID, campo y ruta sin ancla para las referencias del repositorio."""
    for collection in (*COLLECTIONS, "product_verdict", "as_of"):
        value = state.get(collection)
        items = (value,) if isinstance(value, dict) else records(state, collection)
        for record in items:
            for field in REFERENCE_FIELDS:
                for reference in reference_entries(record, field):
                    if is_repo_path(reference):
                        yield _entry_id(record, collection), field, reference.split("#", 1)[0]
