"""Pruebas del estado, la generación de Markdown y las interfaces de CI."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.governance import sync_docs
from scripts.governance.governance_lib import REPO_ROOT, STATE_PATH, Record, validate_state
from scripts.governance.sync_docs import MILESTONES_DOC, STATUS_DOC, TASKS_DOC

DOCUMENTS = {
    STATUS_DOC: ("state-summary",),
    MILESTONES_DOC: ("phases-table", "milestones-table"),
    TASKS_DOC: ("backlog-index",),
}


def _fixture() -> Record:
    statuses = {
        "implementation_status": "PLANNED",
        "review_status": "NOT_REVIEWED",
        "integration_status": "NOT_INTEGRATED",
        "deployment_status": "NOT_DEPLOYED",
    }
    return {
        "schema_version": 1,
        "as_of": {"date": "2024-02-29", "origin_main": "UNKNOWN"},
        "vocab": {
            "implementation_status": [
                "PLANNED", "NOT_STARTED", "IN_PROGRESS", "IMPLEMENTED",
                "IMPLEMENTED_WITH_OPEN_GATE", "BLOCKED",
            ],
            "review_status": ["NOT_REVIEWED", "APPROVED"],
            "integration_status": ["NOT_INTEGRATED", "MERGED"],
            "deployment_status": ["NOT_DEPLOYED", "NOT_APPLICABLE", "STAGING", "PUBLIC"],
            "closure": ["OPEN", "CLOSED"],
            "human_gate_status": ["OPEN", "APPROVED_BY_OWNER"],
        },
        "tasks": [{
            "id": "MP-023", "title": "Captura | verificación", "track": "PRODUCT",
            "depends_on": [], "executor": "claude", "reviewer": "codex", "head": "UNKNOWN",
            "evidence": [], "source": "docs/STATUS.md#artefactos", **statuses,
        }],
        "milestones": [{"id": "H4", "tasks": ["MP-023"], "closure": "OPEN", **statuses}],
        "phases": [{"id": "F0", "tasks": ["MP-023"], "closure": "OPEN",
                    "implementation_status": "PLANNED", "source": "docs/STATUS.md#artefactos"}],
        "proposed_extensions": [{"id": "PROPOSAL-MP-036", "title": "Otra tarea", "status": "PROPOSED"}],
        "human_gates": [{"id": "HG-LIVE-PUBLIC", "status": "OPEN"}],
        "open_findings": [],
        "product_verdict": {"public_deployment": "NO-GO"},
    }


class StateTests(unittest.TestCase):
    """Ejercita las reglas del validador con estados en memoria."""

    def setUp(self) -> None:
        """Prepara un estado válido para cada prueba."""
        self.state = _fixture()
        self.task = self.state["tasks"][0]
        self.phase = self.state["phases"][0]
        self.milestone = self.state["milestones"][0]
        self.gate = self.state["human_gates"][0]

    def _assert_errors(self, *expected: str) -> None:
        errors = "\n".join(validate_state(self.state))
        for fragment in expected:
            self.assertIn(fragment, errors)

    def test_schema_and_vocab(self) -> None:
        """Valida la versión y los estados según sus vocabularios."""
        self.state["schema_version"] = True
        self.task["deployment_status"] = "LIVE"
        self.gate["status"] = "APPROVED"
        self._assert_errors("schema_version", "MP-023: deployment_status fuera de vocab",
                            "HG-LIVE-PUBLIC: status fuera de vocab")

    def test_duplicate_ids(self) -> None:
        """Detecta duplicados de tarea y colisiones entre colecciones."""
        self.state["tasks"].append(self.task.copy())
        self.state["proposed_extensions"].append({"id": "F0"})
        self._assert_errors("MP-023: ID duplicado", "F0: ID duplicado")

    def test_missing_dependencies_and_cycle(self) -> None:
        """Comprueba dependencias, referencias de fase e hito, y ciclos."""
        second = dict(self.task, id="MP-024", depends_on=["MP-023"])
        self.task["depends_on"] = ["MP-999", "MP-024"]
        self.state["tasks"].append(second)
        self.phase["tasks"] = ["MP-998"]
        self.milestone["tasks"] = ["MP-997"]
        self._assert_errors("MP-023: depends_on referencia una tarea inexistente: 'MP-999'",
                            "MP-023 → MP-024 → MP-023", "F0: tasks referencia",
                            "H4: tasks referencia")

    def test_approved_without_reviewer(self) -> None:
        """Una revisión aprobada exige revisor y evidencia."""
        self.task.update(review_status="APPROVED", reviewer="   ")
        self._assert_errors("MP-023: APPROVED exige reviewer", "MP-023: APPROVED exige evidence")

    def test_self_review_and_unstarted_task(self) -> None:
        """Impide aprobarse a sí mismo y aprobar o integrar tareas planificadas."""
        self.task.update(review_status="APPROVED", reviewer=" CLAUDE ",
                         integration_status="MERGED", merge_sha="1234567")
        self._assert_errors("reviewer distinto de executor", "PLANNED es incompatible con APPROVED",
                            "PLANNED es incompatible con MERGED")

    def test_implemented_without_evidence(self) -> None:
        """Exige ejecutor, revisor y evidencia al implementar."""
        self.task.update(implementation_status="IMPLEMENTED", executor="", reviewer="", evidence=[" "])
        self._assert_errors("IMPLEMENTED exige executor", "IMPLEMENTED exige reviewer",
                            "IMPLEMENTED exige evidence")

    def test_implemented_and_approved_without_evidence(self) -> None:
        """Informa por separado del requisito de cada estado."""
        self.task.update(implementation_status="IMPLEMENTED", review_status="APPROVED")
        self._assert_errors("MP-023: IMPLEMENTED exige evidence", "MP-023: APPROVED exige evidence")

    def test_closed_phase_without_gate(self) -> None:
        """Comprueba el gate, su evidencia y el estado al cerrar una fase."""
        self.phase.update(closure="CLOSED", implementation_status="IMPLEMENTED_WITH_OPEN_GATE")
        self._assert_errors("F0: CLOSED exige exit_gate", "F0: CLOSED exige gate_evidence",
                            "F0: CLOSED es incompatible con IMPLEMENTED_WITH_OPEN_GATE")

    def test_closed_milestone_with_planned_tasks(self) -> None:
        """Exige gate, evidencia y tareas avanzadas al cerrar un hito."""
        self.milestone.update(closure="CLOSED", gate_evidence=["", "  "])
        self._assert_errors("H4: CLOSED exige gate", "H4: CLOSED exige gate_evidence",
                            "H4: CLOSED contiene MP-023 en PLANNED")

    def test_closed_milestone_with_valid_inherited_gates(self) -> None:
        """Admite el cierre histórico con fases abiertas identificadas."""
        self.task.update(implementation_status="IMPLEMENTED", evidence=["docs/STATUS.md"])
        self.milestone.update(
            closure="CLOSED", implementation_status="IMPLEMENTED_WITH_OPEN_GATE",
            gate="Registro histórico", gate_evidence=["docs/STATUS.md"], open_gates_inherited=["F0"],
        )
        self.assertEqual(validate_state(self.state), [])

    def test_closed_milestone_with_invalid_inherited_gates(self) -> None:
        """Rechaza sin fases heredadas, con fases inexistentes o cerradas."""
        self.task.update(implementation_status="IMPLEMENTED", evidence=["docs/STATUS.md"])
        self.phase.update(closure="CLOSED", exit_gate="Cerrado", gate_evidence="docs/STATUS.md")
        self.milestone.update(
            closure="CLOSED", implementation_status="IMPLEMENTED_WITH_OPEN_GATE",
            gate="Registro histórico", gate_evidence=["docs/STATUS.md"],
        )
        self._assert_errors("H4: CLOSED con IMPLEMENTED_WITH_OPEN_GATE exige open_gates_inherited")
        self.milestone["open_gates_inherited"] = []
        self._assert_errors("H4: CLOSED con IMPLEMENTED_WITH_OPEN_GATE exige open_gates_inherited")
        self.milestone["open_gates_inherited"] = ["F99", "F0"]
        self._assert_errors("H4: open_gates_inherited referencia una fase inexistente: 'F99'",
                            "H4: open_gates_inherited exige que F0 esté OPEN")

    def test_sha_and_date_formats(self) -> None:
        """Verifica el SHA de merge, el HEAD y las fechas del calendario."""
        self.task.update(integration_status="MERGED", merge_sha="UNKNOWN", head="ab123",
                         review_date="2024-02-30")
        self.milestone.update(integration_status="MERGED", merge={"sha": "abcdefg", "date": "20241125"})
        self._assert_errors("MP-023: MERGED exige merge_sha", "MP-023: head debe",
                            "MP-023: review_date debe", "H4: MERGED exige merge.sha",
                            "H4 (merge): date debe")

    def test_unknown_is_valid_for_optional_metadata(self) -> None:
        """Admite UNKNOWN en HEAD y fechas cuyo valor todavía se desconoce."""
        self.task.update(review_date="UNKNOWN", merge_sha="UNKNOWN")
        self.assertEqual(validate_state(self.state), [])

    def test_human_gate_without_approval_fields(self) -> None:
        """Exige autoría humana, fecha real y evidencia de una aprobación."""
        self.gate.update(status="APPROVED_BY_OWNER", date="UNKNOWN")
        self._assert_errors("HG-LIVE-PUBLIC: APPROVED_BY_OWNER exige approved_by",
                            "HG-LIVE-PUBLIC: APPROVED_BY_OWNER exige date",
                            "HG-LIVE-PUBLIC: APPROVED_BY_OWNER exige evidence")

    def test_human_gate_approved_by_someone_else(self) -> None:
        """Rechaza que otra persona se registre como aprobadora."""
        self.gate.update(status="APPROVED_BY_OWNER", date="2026-11-25",
                         evidence=["docs/STATUS.md"], approved_by="reviewer")
        self._assert_errors("HG-LIVE-PUBLIC: APPROVED_BY_OWNER exige approved_by = owner")

    def test_deployment_evidence_public_gate_and_verdict(self) -> None:
        """Exige evidencia de despliegue y aplica ambos requisitos de publicidad."""
        self.task["deployment_status"] = "STAGING"
        self.milestone["deployment_status"] = "PUBLIC"
        self._assert_errors("MP-023: STAGING exige deployment_evidence", "H4: PUBLIC exige deployment_evidence",
                            "H4: PUBLIC exige un deployment_gate existente", "H4: PUBLIC exige HG-LIVE-PUBLIC",
                            "H4: PUBLIC es incompatible con el veredicto NO-GO")
        self.task["deployment_evidence"] = ["docs/STATUS.md"]
        self.milestone.update(deployment_gate="HG-LIVE-PUBLIC", deployment_evidence=["docs/STATUS.md"])
        self.gate.update(status="APPROVED_BY_OWNER", approved_by="owner",
                         date="2026-11-25", evidence=["docs/STATUS.md"])
        self.state["product_verdict"]["public_deployment"] = "GO"
        self.assertEqual(validate_state(self.state), [])

    def test_mvp0_public_rejects_approved_tiles_gate_without_publish_approval(self) -> None:
        """Una aprobación de teselas no autoriza publicar MVP0."""
        self.state["human_gates"].extend([
            {"id": "HG-MVP0-PUBLISH", "status": "OPEN"},
            {"id": "HG-TILES", "status": "APPROVED_BY_OWNER", "approved_by": "owner",
             "date": "2026-11-25", "evidence": ["docs/STATUS.md"]},
        ])
        self.task.update(milestone="MVP0", deployment_status="PUBLIC", deployment_evidence=["docs/STATUS.md"],
                         deployment_gate="HG-TILES")
        self.milestone.update(id="MVP0", deployment_status="PUBLIC", deployment_evidence=["docs/STATUS.md"],
                              deployment_gate="HG-TILES")
        self.assertEqual(validate_state(self.state), [
            "MP-023: PUBLIC exige HG-MVP0-PUBLISH en APPROVED_BY_OWNER con aprobación válida",
            "MVP0: PUBLIC exige HG-MVP0-PUBLISH en APPROVED_BY_OWNER con aprobación válida",
        ])

    def test_mvp0_public_uses_its_own_gate_under_no_go(self) -> None:
        """La demo requiere aprobación propia aunque siga vigente el NO-GO Live."""
        gate = {
            "id": "HG-DEMO", "status": "APPROVED_BY_OWNER", "approved_by": "owner",
            "date": "2026-11-25", "evidence": ["docs/STATUS.md"],
        }
        self.state["human_gates"].extend([gate, dict(gate, id="HG-MVP0-PUBLISH")])
        self.task.update(track="MVP0", deployment_status="PUBLIC", deployment_evidence=["docs/STATUS.md"],
                         deployment_gate="HG-DEMO")
        self.milestone.update(id="MVP0", deployment_status="PUBLIC", deployment_evidence=["docs/STATUS.md"],
                              deployment_gate="HG-DEMO")
        self.assertEqual(validate_state(self.state), [])
        gate["approved_by"] = "reviewer"
        self._assert_errors("MP-023: PUBLIC exige deployment_gate HG-DEMO en APPROVED_BY_OWNER",
                            "MVP0: PUBLIC exige deployment_gate HG-DEMO en APPROVED_BY_OWNER")
        gate["approved_by"] = "owner"
        self.task["track"] = "PRODUCT"
        self.milestone["id"] = "H4"
        self._assert_errors("MP-023: PUBLIC exige HG-LIVE-PUBLIC", "H4: PUBLIC exige HG-LIVE-PUBLIC",
                            "MP-023: PUBLIC es incompatible con el veredicto NO-GO",
                            "H4: PUBLIC es incompatible con el veredicto NO-GO")

    def _alias(self, *, task_id: str = "D-01", target: str = "MP-023") -> Record:
        alias = dict(self.task, id=task_id, alias_of=target)
        self.state["tasks"].append(alias)
        return alias

    def test_valid_alias(self) -> None:
        """Admite un alias que apunta a una tarea canónica."""
        self._alias()
        self.assertEqual(validate_state(self.state), [])

    def test_alias_target_missing(self) -> None:
        """Rechaza un alias cuyo identificador canónico no existe."""
        self._alias(target="MP-999")
        self._assert_errors("D-01: alias_of referencia una tarea inexistente")

    def test_alias_chains_and_self_aliases(self) -> None:
        """Impide cadenas de alias y referencias a sí mismo."""
        self._alias()
        self._alias(task_id="D-02", target="D-01")
        self._alias(task_id="D-03", target="D-03")
        self._assert_errors("D-02: alias_of referencia el alias D-01",
                            "D-03: alias_of no puede referenciar la misma tarea")

    def test_dependency_on_alias(self) -> None:
        """Exige que las dependencias apunten al identificador canónico."""
        self._alias()
        self.state["tasks"].append(dict(self.task, id="MP-024", depends_on=["D-01"]))
        self._assert_errors("MP-024: depends_on referencia el alias D-01")

    def test_required_gates_exist(self) -> None:
        """Los gates requeridos deben existir aunque estén abiertos."""
        self.task["requires_gates"] = ["HG-LIVE-PUBLIC", "HG-MISSING"]
        self._assert_errors("MP-023: requires_gates referencia una puerta humana inexistente: 'HG-MISSING'")
        self.task["requires_gates"].pop()
        self.assertEqual(validate_state(self.state), [])

    def test_reference_rejects_escape_absolute_schemes_and_prose(self) -> None:
        """Solo admite referencias del repositorio y UNKNOWN en campos de evidencia."""
        self.task.update(evidence=["docs/../../externo.md", "/tmp/externo.md",
                                  r"C:\externo.md", "https://example.test/fuente"],
                         source="Acta de la reunión", notes="Acta de la reunión")
        self.phase["gate_evidence"] = "Acta de la fase"
        self._assert_errors(
            "MP-023: evidence: ruta que escapa del repositorio", "MP-023: evidence: ruta absoluta",
            "MP-023: evidence: esquema de URL", "MP-023: source: se exige una ruta",
            "F0: gate_evidence: se exige una ruta",
        )
        errors = validate_state(self.state)
        self.assertEqual(sum("ruta absoluta" in error for error in errors), 2)
        self.assertFalse(any(": notes:" in error for error in errors))


def _run_script(root: Path, script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(root / "scripts/governance" / script), *args],
        cwd=root.parent, capture_output=True, text=True, check=False,
    )


class CliTests(unittest.TestCase):
    """Ejecuta ambas interfaces en una copia temporal mínima."""

    def setUp(self) -> None:
        """Crea archivos aislados y ejecuta desde fuera de su raíz."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        shutil.copytree(REPO_ROOT / "scripts/governance", self.root / "scripts/governance",
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.state = _fixture()
        (self.root / STATE_PATH).parent.mkdir(parents=True)
        self._write_state()
        for name, blocks in DOCUMENTS.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "Preámbulo\n" + "".join(
                    f"<!-- BEGIN GENERATED: {block} -->\n<!-- END GENERATED: {block} -->\nTexto intermedio\n"
                    for block in blocks
                ) + "Epílogo",
                encoding="utf-8",
            )

    def _write_state(self) -> None:
        (self.root / STATE_PATH).write_text(json.dumps(self.state), encoding="utf-8")

    def _sync(self, *args: str) -> subprocess.CompletedProcess[str]:
        return _run_script(self.root, "sync_docs.py", *args)

    def _assert_synced(self) -> None:
        result = self._sync()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_json(self) -> None:
        """El comprobador rechaza constantes ajenas a JSON."""
        (self.root / STATE_PATH).write_text('{"schema_version": NaN}', encoding="utf-8")
        result = _run_script(self.root, "check_docs.py")
        self.assertEqual(result.returncode, 1)
        self.assertIn("PROJECT_STATE.json", result.stderr)
        self.assertIn("NaN", result.stderr)

    def test_drift_is_detected_and_fixed(self) -> None:
        """Detecta la alteración sin escribir y comprueba la reparación."""
        self._assert_synced()
        path = self.root / STATUS_DOC
        stale = path.read_bytes().replace(b"CI verde", b"CI alterada")
        path.write_bytes(stale)
        check = self._sync("--check")
        self.assertEqual(check.returncode, 1)
        self.assertIn("-**DONE ≠ MERGED ≠ LIVE. CI alterada", check.stdout)
        self.assertEqual(path.read_bytes(), stale)
        result = _run_script(self.root, "check_docs.py")
        self.assertEqual(result.returncode, 1)
        self.assertIn("bloques desincronizados", result.stderr)
        self._assert_synced()
        self.assertEqual(self._sync("--check").returncode, 0)
        self.assertEqual(_run_script(self.root, "check_docs.py").returncode, 0)

    def test_repeatable_sync_and_rendering(self) -> None:
        """Comprueba bytes y contenido tras dos regeneraciones independientes."""
        originals = {name: (self.root / name).read_bytes() for name in DOCUMENTS}
        self._assert_synced()
        first = {name: (self.root / name).read_bytes() for name in DOCUMENTS}
        for name, contents in originals.items():
            (self.root / name).write_bytes(contents)
        self._assert_synced()
        second = {name: (self.root / name).read_bytes() for name in DOCUMENTS}
        self.assertEqual(first, second)
        self.assertIn(r"Captura \| verificación", first[TASKS_DOC].decode())
        self.assertIn("[docs/STATUS.md#artefactos](../STATUS.md#artefactos)", first[MILESTONES_DOC].decode())
        self.assertIn("PROPUESTA sin ID asignado", first[TASKS_DOC].decode())
        self.assertNotIn("PROPOSAL-MP-036", first[TASKS_DOC].decode())

    def test_preserves_external_bytes_and_state(self) -> None:
        """Preserva CRLF, marcadores, texto ajeno al bloque y el estado JSON."""
        path = self.root / STATUS_DOC
        prefix = b"Pre\r\n<!-- BEGIN GENERATED: state-summary -->  \r\n"
        suffix = b"<!-- END GENERATED: state-summary -->\nFinal"
        path.write_bytes(prefix + b"contenido anterior\r\n" + suffix)
        self.state["human_gates"][0].update(
            status="APPROVED_BY_OWNER", approved_by="owner", date="2026-11-25", evidence=["docs/STATUS.md"],
        )
        self._write_state()
        state_bytes = (self.root / STATE_PATH).read_bytes()
        self._assert_synced()
        self.assertTrue(path.read_bytes().startswith(prefix))
        self.assertTrue(path.read_bytes().endswith(suffix))
        self.assertEqual((self.root / STATE_PATH).read_bytes(), state_bytes)
        self.assertEqual(self._sync("--check").returncode, 0)

    def test_missing_marker(self) -> None:
        """Devuelve 2 en ambos modos y conserva todos los archivos."""
        (self.root / TASKS_DOC).write_text("Sin marcador\n", encoding="utf-8")
        before = {name: (self.root / name).read_bytes() for name in DOCUMENTS}
        for args in ((), ("--check",)):
            with self.subTest(args=args):
                result = self._sync(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("backlog-index: falta un marcador", result.stderr)
                self.assertEqual(before, {name: (self.root / name).read_bytes() for name in DOCUMENTS})

    def test_duplicate_and_nested_markers(self) -> None:
        """Un marcador duplicado o anidado aborta la actualización completa."""
        path = self.root / TASKS_DOC
        begin = b"<!-- BEGIN GENERATED: backlog-index -->\n"
        end = b"<!-- END GENERATED: backlog-index -->\n"
        nested = b"<!-- BEGIN GENERATED: otro -->\n<!-- END GENERATED: otro -->\n"
        for body, fragment in ((begin * 2 + end, "duplicado"), (begin + nested + end, "anidados")):
            with self.subTest(fragment=fragment):
                path.write_bytes(body)
                before = {name: (self.root / name).read_bytes() for name in DOCUMENTS}
                result = self._sync()
                self.assertEqual(result.returncode, 2)
                self.assertIn(fragment, result.stderr)
                self.assertEqual(before, {name: (self.root / name).read_bytes() for name in DOCUMENTS})

    def test_atomic_sync_rolls_back_after_second_replace_fails(self) -> None:
        """Conserva todos los bytes y elimina temporales si falla un reemplazo."""
        before = {name: (self.root / name).read_bytes() for name in DOCUMENTS}
        replace = os.replace
        snapshots = []

        def fail_second(source: str | Path, target: str | Path) -> None:
            source_path, target_path = Path(source), Path(target)
            self.assertEqual(source_path.parent, target_path.parent)
            if target_path == self.root / MILESTONES_DOC:
                snapshots.append((self.root / STATUS_DOC).read_bytes())
                raise OSError("fallo simulado al reemplazar el segundo documento")
            replace(source, target)

        stderr = StringIO()
        with patch.object(sync_docs.os, "replace", side_effect=fail_second), redirect_stderr(stderr):
            self.assertEqual(sync_docs.sync(self.root, self.state, check=False), 2)
        self.assertEqual(len(snapshots), 1)
        self.assertIn(b"DONE", snapshots[0])
        self.assertIn("fallo simulado", stderr.getvalue())
        self.assertEqual(before, {name: (self.root / name).read_bytes() for name in DOCUMENTS})
        self.assertEqual(list((self.root / "docs").rglob(".*.md.*")), [])
        self._assert_synced()

    def test_alias_render_is_separate_and_excluded_from_counts(self) -> None:
        """Cada tarea canónica cuenta una vez y su alias se ve en otra tabla."""
        task = self.state["tasks"][0]
        self.state["tasks"].append(dict(task, id="D-01", title="Alias de captura", alias_of="MP-023"))
        self._write_state()
        self._assert_synced()
        summary = (self.root / STATUS_DOC).read_text(encoding="utf-8")
        self.assertIn("| implementation_status | PLANNED | 1 |", summary)
        self.assertIn("| review_status | NOT_REVIEWED | 1 |", summary)
        self.assertIn("| integration_status | NOT_INTEGRATED | 1 |", summary)
        self.assertIn("| deployment_status | NOT_DEPLOYED | 1 |", summary)
        backlog = (self.root / TASKS_DOC).read_text(encoding="utf-8")
        canonical, aliases = backlog.split("### Alias (mismo trabajo, otro identificador)")
        self.assertIn("| MP-023 |", canonical)
        self.assertNotIn("| D-01 |", canonical)
        self.assertIn("| D-01 | MP-023 | Alias de captura |", aliases)

    def test_render_audit_metadata_limits_and_literal_anchors(self) -> None:
        """Distingue baseline, integración, evidencia y cobertura de hallazgos."""
        self.state["as_of"].update(baseline_tag="h3-local-audited", origin_main="7583ca5",
                                   product_baseline_head="beb9434")
        self.state["milestones"][0].update(
            closure="CLOSED", integration_kind="content_in_main", merge={"pr": 42, "sha": "7583ca5"},
            evidence_limit="Sin validación remota", open_gates_inherited=["F0", "F1"],
        )
        self.state["phases"][0].update(evidence_limit="Ventana de 23 h")
        self.state["tasks"][0].update(
            integration_kind="content_in_main", pr=43, evidence=["docs/STATUS.md#secci%C3%B3n"],
        )
        self.state["tasks"].append(dict(self.state["tasks"][0], id="MP-024", integration_kind="merge_commit", pr=44))
        self._write_state()
        self._assert_synced()
        summary = (self.root / STATUS_DOC).read_text(encoding="utf-8")
        self.assertIn("Etiqueta `h3-local-audited` → `7583ca5`.\n\nBaseline de producto auditado: `beb9434`.", summary)
        self.assertIn("Universo completo de hallazgos: `docs/audits/hito-03/FINDINGS_REGISTER.md` (hasta MP-034).", summary)
        milestones = (self.root / MILESTONES_DOC).read_text(encoding="utf-8")
        self.assertIn("cierre histórico; gates abiertos heredados: F0, F1", milestones)
        self.assertEqual(milestones.count("Límite de la evidencia"), 2)
        self.assertIn("Ventana de 23 h", milestones)
        self.assertIn("Sin validación remota", milestones)
        self.assertIn("incorporado a main (no fusión de rama) · 7583ca5", milestones)
        self.assertNotIn("PR #42", milestones)
        backlog = (self.root / TASKS_DOC).read_text(encoding="utf-8")
        self.assertIn("incorporado a main (no fusión de rama)", backlog)
        self.assertNotIn("PR #43", backlog)
        self.assertIn("PR #44", backlog)
        self.assertIn("(STATUS.md#secci%C3%B3n)", backlog)

    def test_added_repo_roots_and_symlink_escape(self) -> None:
        """Verifica rutas de raíz, sus anclas y escapes por enlace simbólico."""
        paths = [".github/workflows/ci.yml", "README.md", "AGENTS.md", "CLAUDE.md", "LICENSE-EXAMPLE", "NOTICE.md"]
        for relative in paths:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        task = self.state["tasks"][0]
        task["evidence"] = [f"{path}#ancla" for path in paths]
        task["evidence"].append("docs/../README.md#ancla")
        self._write_state()
        self._assert_synced()
        result = _run_script(self.root, "check_docs.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.root / "docs/externo").symlink_to(self.root.parent, target_is_directory=True)
        task["evidence"].append("docs/externo")
        self._write_state()
        self._assert_synced()
        result = _run_script(self.root, "check_docs.py")
        self.assertEqual(result.returncode, 1)
        self.assertIn("MP-023: evidence: ruta que escapa del repositorio: docs/externo", result.stderr)

    def test_missing_reference_and_heading(self) -> None:
        """Comprueba referencias sin ancla y el encabezado de la tarea."""
        task = self.state["tasks"][0]
        task.update(source=TASKS_DOC, evidence=["docs/ausente.md#evidencia", "UNKNOWN"])
        self._write_state()
        self._assert_synced()
        result = _run_script(self.root, "check_docs.py")
        self.assertEqual(result.returncode, 1)
        self.assertIn("MP-023: evidence apunta a una ruta inexistente: docs/ausente.md\n", result.stderr)
        self.assertIn("MP-023: falta el encabezado", result.stderr)
        (self.root / "docs/ausente.md").touch()
        with (self.root / TASKS_DOC).open("a", encoding="utf-8") as backlog:
            backlog.write("\n## MP-023 — Descripción\n")
        result = _run_script(self.root, "check_docs.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class RepositoryTests(unittest.TestCase):
    """Comprueba que el estado real cumple el mismo contrato que las fixtures."""

    def test_project_state_passes_check_docs(self) -> None:
        """Ejecuta el comprobador sobre el repositorio real en modo de lectura."""
        result = _run_script(REPO_ROOT, "check_docs.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
