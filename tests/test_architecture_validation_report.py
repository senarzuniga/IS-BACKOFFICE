import unittest
from pathlib import Path
import re


class TestArchitectureValidationReport(unittest.TestCase):

    def test_generate_architecture_validation_report(self):
        root = Path.cwd()
        report_path = root / 'ARCHITECTURE_VALIDATION_REPORT.md'

        py_files = [p for p in root.rglob('*.py') if 'tests' not in str(p)]

        files_with_openai = []
        files_with_sqlite_connect = []
        ui_files = [p for p in root.glob('pages/*.py')]
        ui_access_memory = []
        ui_import_workers = []

        for p in py_files:
            try:
                text = p.read_text(encoding='utf8')
            except Exception:
                text = ''
            if 'openai' in text:
                files_with_openai.append(str(p.relative_to(root)))
            if 'sqlite3.connect' in text:
                files_with_sqlite_connect.append(str(p.relative_to(root)))

        for p in ui_files:
            try:
                t = p.read_text(encoding='utf8')
            except Exception:
                t = ''
            if 'memory_store' in t or 'MemoryStore' in t:
                ui_access_memory.append(str(p.relative_to(root)))
            if 'WorkerManager' in t or 'workers' in t:
                ui_import_workers.append(str(p.relative_to(root)))

        # Check that ai_orchestrator wires evidence and fact checker
        ai_file = root / 'soc' / 'brain' / 'ai_orchestrator.py'
        ai_text = ai_file.read_text(encoding='utf8') if ai_file.exists() else ''
        evidence_called = 'collect_evidence' in ai_text
        factchecker_called = 'assess_evidence' in ai_text
        context_router_used = 'ContextRouter' in ai_text

        report_lines = []
        report_lines.append('# Architecture Validation Report')
        report_lines.append('')
        report_lines.append('## Findings')
        report_lines.append('')
        report_lines.append(f'- Direct LLM libraries found: {len(files_with_openai)}')
        for f in files_with_openai:
            report_lines.append(f'  - {f}')
        report_lines.append(f'- Files with sqlite3.connect calls: {len(files_with_sqlite_connect)}')
        for f in files_with_sqlite_connect:
            report_lines.append(f'  - {f}')
        report_lines.append(f'- UI files accessing MemoryStore: {len(ui_access_memory)}')
        for f in ui_access_memory:
            report_lines.append(f'  - {f}')
        report_lines.append(f'- UI files importing workers: {len(ui_import_workers)}')
        for f in ui_import_workers:
            report_lines.append(f'  - {f}')
        report_lines.append(f'- ai_orchestrator uses ContextRouter: {context_router_used}')
        report_lines.append(f'- ai_orchestrator calls collect_evidence: {evidence_called}')
        report_lines.append(f'- ai_orchestrator calls assess_evidence: {factchecker_called}')

        # Summary and verdicts
        report_lines.append('')
        report_lines.append('## Verdict')
        report_lines.append('')
        if files_with_openai:
            report_lines.append('- Direct LLM usage detected — FAIL (must be mediated).')
        else:
            report_lines.append('- No direct LLM libraries detected — PASS')

        if ui_access_memory:
            report_lines.append('- UI accesses MemoryStore directly — FAIL')
        else:
            report_lines.append('- UI does not access MemoryStore directly — PASS')

        if not context_router_used:
            report_lines.append('- ContextRouter not used by orchestrator — FAIL')
        else:
            report_lines.append('- ContextRouter used by orchestrator — PASS')

        if not evidence_called or not factchecker_called:
            report_lines.append('- Evidence/FactChecker not executed in orchestrator — FAIL')
        else:
            report_lines.append('- Evidence and FactChecker executed in orchestrator — PASS')

        if len(files_with_sqlite_connect) > 1:
            report_lines.append('- Multiple sqlite3.connect usage detected — NOTE (investigate other persistent stores).')
        else:
            report_lines.append('- sqlite3.connect usage is localized — PASS')

        report_path.write_text('\n'.join(report_lines), encoding='utf8')
        self.assertTrue(report_path.exists())


if __name__ == '__main__':
    unittest.main()
