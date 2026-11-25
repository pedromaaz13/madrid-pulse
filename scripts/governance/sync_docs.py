"""Sincroniza los bloques Markdown derivados del estado canónico."""

import argparse
import difflib
import posixpath
import re
import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import quote

if __package__:
    from .governance_lib import (
        REPO_ROOT, STATE_PATH, STATUS_FIELDS, Record, is_repo_path, load_state,
        records, reference_entries, text_entries,
    )
else:
    from governance_lib import (
        REPO_ROOT, STATE_PATH, STATUS_FIELDS, Record, is_repo_path, load_state,
        records, reference_entries, text_entries,
    )


STATUS_DOC = "docs/STATUS.md"
MILESTONES_DOC = "docs/roadmap/MILESTONES.md"
TASKS_DOC = "docs/TASKS.md"
HISTORICAL_TASKS = {f"MP-{number:03d}" for number in range(1, 23)}
MARKER = re.compile(rb"^<!-- (BEGIN|END) GENERATED: ([^\r\n]+?) -->[ \t]*(?:\r?\n|$)", re.MULTILINE)


def _text(value: object) -> str:
    if value is None or value == "" or value == []:
        return "—"
    if isinstance(value, list):
        return ", ".join(map(str, value))
    return str(value)


def _cell(value: object) -> str:
    text = " ".join(_text(value).splitlines())
    return re.sub(r"(\\*)\|", lambda match: match[1] * 2 + r"\|", text)


def _table(headers: Iterable[str], rows: Iterable[Iterable[object]]) -> str:
    columns = list(headers)
    return "\n".join(
        "| " + " | ".join(map(_cell, row)) + " |"
        for row in (columns, ["---"] * len(columns), *rows)
    )


def _refs(record: Record, field: str, document: str) -> str:
    links = []
    for reference in reference_entries(record, field):
        if is_repo_path(reference):
            path, separator, anchor = reference.partition("#")
            relative = posixpath.relpath(path, posixpath.dirname(document))
            destination = quote(relative, safe="/") + separator + quote(anchor)
            label = reference.replace("[", r"\[").replace("]", r"\]")
            links.append(f"[{label}]({destination})")
        else:
            links.append(reference)
    return "; ".join(links) or "—"


def _milestones(state: Record, document: str) -> str:
    rows = []
    for milestone in records(state, "milestones"):
        merge = milestone.get("merge")
        if not isinstance(merge, dict):
            merge = {}
        merge_text = " · ".join(
            str(value)
            for value in (f"#{merge['pr']}" if merge.get("pr") is not None else None,
                          merge.get("sha"), merge.get("date"))
            if value is not None
        )
        rows.append((
            milestone.get("id"), milestone.get("title"),
            *(milestone.get(field) for field in STATUS_FIELDS), milestone.get("closure"),
            merge_text, milestone.get("gate"), _refs(milestone, "gate_evidence", document),
        ))
    return _table(
        ("ID", "Hito", *STATUS_FIELDS, "closure", "Merge (PR · SHA · fecha)", "Gate", "Evidencia"),
        rows,
    )


def _phases(state: Record) -> str:
    return _table(
        ("ID", "Fase", "Tareas", "implementation_status", "closure", "Hallazgos abiertos",
         "Evidencia del gate", "Fuente"),
        (
            (phase.get("id"), phase.get("title"), phase.get("tasks"), phase.get("implementation_status"),
             phase.get("closure"), phase.get("open_findings"),
             _refs(phase, "gate_evidence", MILESTONES_DOC),
             _refs(phase, "source", MILESTONES_DOC))
            for phase in records(state, "phases")
        ),
    )


def _backlog(state: Record) -> str:
    rows = []
    for task in records(state, "tasks"):
        task_id = task.get("id")
        if isinstance(task_id, str) and task_id in HISTORICAL_TASKS:
            continue
        relationships = "; ".join(
            f"{label} {_text(task[field])}"
            for field, label in (("aliases", "Alias"), ("related", "Relacionadas"))
            if task.get(field)
        )
        rows.append((
            task_id, task.get("title"), task.get("track"), task.get("implementation_status"),
            task.get("depends_on"), task.get("executor"), task.get("reviewer"), relationships,
            _refs(task, "source", TASKS_DOC), _refs(task, "evidence", TASKS_DOC),
        ))
    extensions = []
    for item in records(state, "proposed_extensions"):
        proposal = (
            f"- **PROPUESTA sin ID asignado** · {_cell(item.get('title'))}. {_cell(item.get('reason'))}"
        )
        if item.get("maps_from"):
            proposal += f" Origen: {_cell(item['maps_from'])}."
        extensions.append(proposal)
    table = _table(
        ("ID", "Título", "Track", "implementation_status", "Dependencias", "Ejecutor", "Revisor",
         "Alias y relaciones", "Fuente", "Evidencia"),
        rows,
    )
    return "\n\n".join([table, "### Extensiones propuestas", "\n".join(extensions) or "—"])


def _summary(state: Record) -> str:
    as_of = state.get("as_of")
    if not isinstance(as_of, dict):
        as_of = {}
    verdict = state.get("product_verdict")
    if not isinstance(verdict, dict):
        verdict = {}
    vocab = state.get("vocab")
    if not isinstance(vocab, dict):
        vocab = {}
    counts = []
    for field in STATUS_FIELDS:
        tally = Counter(_text(task.get(field)) for task in records(state, "tasks"))
        counts.extend((field, status, tally[status]) for status in text_entries(vocab.get(field)))
    findings = _table(
        ("ID", "Severidad", "Hallazgo", "Estado", "Corrección prevista", "Evidencia"),
        ((item.get("id"), item.get("severity"), item.get("title"), item.get("status"),
          item.get("planned_fix"), _refs(item, "evidence", STATUS_DOC))
         for item in records(state, "open_findings")),
    )
    gates = _table(
        ("ID", "Decisión del propietario", "Estado", "Nota"),
        ((gate.get("id"), gate.get("title"), gate.get("status"), gate.get("note"))
         for gate in records(state, "human_gates")),
    )
    return "\n\n".join((
        f"**Estado al {_cell(as_of.get('date'))}.** "
        f"Despliegue público **{_cell(verdict.get('public_deployment'))}** · "
        f"código integrado local **{_cell(verdict.get('local_integrated_code'))}**. "
        f"Fuente: {_cell(_refs(verdict, 'source', STATUS_DOC))}.",
        f"Main: `{_cell(as_of.get('origin_main'))}` · "
        f"línea base: `{_cell(as_of.get('baseline_tag'))}` "
        f"(`{_cell(as_of.get('product_baseline_head'))}`).",
        "**DONE ≠ MERGED ≠ LIVE. CI verde ≠ cero P0.**",
        "### Recuentos de tareas por estado",
        _table(("Dimensión", "Estado", "Tareas"), counts),
        "### Hitos",
        _milestones(state, STATUS_DOC),
        "### Hallazgos abiertos",
        findings,
        "### Decisiones del propietario",
        gates,
    ))


def _replace_blocks(
    path: str, original: bytes, blocks: dict[str, str],
) -> tuple[bytes, list[str]]:
    matches = list(MARKER.finditer(original))
    errors = []
    edits = []
    for name, content in blocks.items():
        encoded_name = name.encode()
        starts = [i for i, match in enumerate(matches) if match.groups() == (b"BEGIN", encoded_name)]
        ends = [i for i, match in enumerate(matches) if match.groups() == (b"END", encoded_name)]
        if len(starts) != 1 or len(ends) != 1:
            errors.append(f"{path}: {name}: falta un marcador requerido o está duplicado (BEGIN={len(starts)}, END={len(ends)})")
            continue
        if ends[0] != starts[0] + 1:
            errors.append(f"{path}: {name}: marcadores desordenados o anidados")
            continue
        start, end = matches[starts[0]], matches[ends[0]]
        newline = b"\r\n" if start.group().endswith(b"\r\n") else b"\n"
        body = content.encode("utf-8").replace(b"\n", newline)
        edits.append((start.end(), end.start(), newline + body + newline * 2))
    updated = original
    for start, end, body in sorted(edits, reverse=True):
        updated = updated[:start] + body + updated[end:]
    return updated, errors


def sync(root: Path, state: Record, *, check: bool) -> int:
    """Comprueba o actualiza los bloques generados en la raíz indicada."""
    documents = {
        STATUS_DOC: {"state-summary": _summary(state)},
        MILESTONES_DOC: {"phases-table": _phases(state), "milestones-table": _milestones(state, MILESTONES_DOC)},
        TASKS_DOC: {"backlog-index": _backlog(state)},
    }
    changes = []
    errors = []
    for name, blocks in documents.items():
        try:
            original = (root / name).read_bytes()
        except OSError as error:
            errors.append(f"{name}: {error}")
            continue
        updated, marker_errors = _replace_blocks(name, original, blocks)
        errors.extend(marker_errors)
        if original != updated:
            changes.append((name, original, updated))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        if not check:
            return 2
    if check:
        for name, original, updated in changes:
            diff = difflib.diff_bytes(
                difflib.unified_diff, original.split(b"\n"), updated.split(b"\n"),
                f"a/{name}".encode(), f"b/{name}".encode(), lineterm=b"",
            )
            for line in diff:
                print(line.decode("utf-8", errors="backslashreplace").replace("\r", r"\r"))
        if errors:
            return 2
        return 1 if changes else 0
    for name, _, updated in changes:
        try:
            (root / name).write_bytes(updated)
        except OSError as error:
            print(f"{name}: {error}", file=sys.stderr)
            return 2
        print(f"Actualizado {name}")
    return 0


def main() -> int:
    """Ejecuta la interfaz de sincronización documental."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="muestra diferencias sin escribir")
    args = parser.parse_args()
    try:
        state = load_state(REPO_ROOT / STATE_PATH)
        return sync(REPO_ROOT, state, check=args.check)
    except (OSError, ValueError) as error:
        print(f"{STATE_PATH}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
