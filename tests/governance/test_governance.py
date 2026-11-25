"""Pruebas del estado, la generación de Markdown y las interfaces de CI."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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

    def test_deployment_evidence_public_gate_and_verdict(self) -> None:
        """Exige evidencia de despliegue y aplica ambos requisitos de publicidad."""
        self.task["deployment_status"] = "STAGING"
        self.milestone["deployment_status"] = "PUBLIC"
        self._assert_errors("MP-023: STAGING exige deployment_evidence", "H4: PUBLIC exige deployment_evidence",
                            "H4: PUBLIC exige HG-LIVE-PUBLIC", "H4: PUBLIC es incompatible con el veredicto NO-GO")
        self.task["deployment_evidence"] = ["ensayo"]
        self.milestone["deployment_evidence"] = ["evidencia de publicación"]
        self.gate.update(status="APPROVED_BY_OWNER", approved_by="owner", date="2026-11-25", evidence=["acta"])
        self.state["product_verdict"]["public_deployment"] = "GO"
        self.assertEqual(validate_state(self.state), [])


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
            status="APPROVED_BY_OWNER", approved_by="owner", date="2026-11-25", evidence=["acta"],
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

    def test_missing_reference_and_heading(self) -> None:
        """Comprueba referencias sin ancla y el encabezado de la tarea."""
        task = self.state["tasks"][0]
        task.update(source=TASKS_DOC, evidence=["docs/ausente.md#evidencia", "https://example.test/fuente"])
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
