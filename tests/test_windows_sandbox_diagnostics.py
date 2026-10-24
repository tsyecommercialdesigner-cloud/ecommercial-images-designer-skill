"""Exercise the real policy query without launching Codex or changing policy."""

import json
import base64
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "nt", "Requires the Windows PowerShell 5.1 OS shell")
class WindowsPolicyDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shell = (
            Path(os.environ["SystemRoot"])
            / "System32/WindowsPowerShell/v1.0/powershell.exe"
        )
        source = (REPO / "scripts/Test-WindowsSandbox76d.ps1").read_text(
            encoding="utf-8"
        )
        block = source.split("$policyQuery = @(\n", 1)[1].split(
            "\n) -join ' '", 1
        )[0]
        parts = []
        for line in block.splitlines():
            match = re.fullmatch(r"\s*'((?:[^']|'')*)'\s*", line)
            if not match:
                raise AssertionError("Expected fixed diagnostic source strings")
            parts.append(match.group(1).replace("''", "'"))
        cls.query = " ".join(parts)
        cls.denial_function = "function Test-SandboxWriteDenial {" + source.split(
            "function Test-SandboxWriteDenial {", 1
        )[1].split("\n$ErrorActionPreference", 1)[0]

    def run_query(self, query, env=None):
        # Native subprocess inheritance reproduces the intermediate-process
        # boundary; PowerShell 7's direct powershell.exe path cleanup cannot apply.
        return subprocess.run(
            [str(self.shell), "-NoProfile", "-NonInteractive", "-Command", query],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=30,
            check=False,
        )

    def test_matching_os_modules_with_conflicting_search_paths(self):
        with tempfile.TemporaryDirectory(prefix="policy-76d-modules-") as folder:
            modules = Path(folder)
            for name in ("Microsoft.PowerShell.Security", "Microsoft.PowerShell.Utility"):
                module_dir = modules / name
                module_dir.mkdir()
                # No executable module content: these incompatible manifests
                # emulate earlier same-name modules in an inherited PS7 path.
                (module_dir / f"{name}.psd1").write_text(
                    "@{ ModuleVersion = '99.0'; PowerShellVersion = '99.0' }",
                    encoding="ascii",
                )
            env = os.environ.copy()
            system_modules = self.shell.parent / "Modules"
            env["PSModulePath"] = f"{modules};{system_modules}"
            proc = self.run_query(self.query, env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)
            self.assertIn(str(modules), result["modulePath"])
            self.assertEqual(result["edition"], "Desktop")
            self.assertTrue(result["version"].startswith("5.1."))
            for field, name in (
                ("securityModule", "Microsoft.PowerShell.Security"),
                ("utilityModule", "Microsoft.PowerShell.Utility"),
            ):
                self.assertEqual(
                    Path(result[field]), system_modules / name / f"{name}.psd1"
                )
            self.assertEqual(len(result["scopes"]), 5)
            self.assertTrue(result["identity"])
            self.assertIn(
                result["effective"],
                {"Restricted", "RemoteSigned", "AllSigned", "Unrestricted", "Bypass"},
            )

    def test_import_failure_retains_context_and_returns_failure(self):
        # Fault injection only affects this test command, never the OS module.
        query = self.query.replace(
            "Microsoft.PowerShell.Security.psd1", "Missing76d.psd1"
        )
        # This case tests error/context propagation, not discovery across the
        # runner's unrelated global module catalog. Missing-module resolution in
        # Windows PowerShell 5.1 can enumerate that inherited catalog and exceed
        # the bounded subprocess timeout on Windows CI. Keep the real import
        # failure and the 30s limit, with the same OS-only path used by the test
        # above; production policy/query code and machine configuration stay intact.
        env = os.environ.copy()
        env['PSModulePath'] = str(self.shell.parent / 'Modules')
        # Windows PowerShell appends default global entries during startup;
        # restrict discovery inside this child after that initialization.
        query = '$env:PSModulePath = $PSHOME + "\\Modules"; ' + query
        proc = self.run_query(query, env)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn('modulePath=' + env['PSModulePath'], proc.stderr)
        self.assertFalse(proc.stdout.strip(), proc.stdout)
        for marker in ("identity=", "psHome=", "modulePath=", "Missing76d.psd1"):
            self.assertIn(marker, proc.stderr)
        self.assertNotIn('"effective"', proc.stderr)

    @staticmethod
    def denial_record(path):
        path_data = base64.b64encode(str(path.resolve()).encode("utf-8")).decode("ascii")
        return (
            "SANDBOX_PROBE_ERROR_V1|operation=Write|"
            "type=System.UnauthorizedAccessException|hresult=-2147024891|"
            f"pathUtf8Base64={path_data}"
        )

    def test_write_denial_requires_typed_record_exit_and_absent_target(self):
        with tempfile.TemporaryDirectory(prefix="write-76d-") as folder:
            root = Path(folder)
            target = root / "商品 & spaces.txt"
            existing = root / "existing.txt"
            existing.write_text("must remain", encoding="ascii")
            marker = self.denial_record(target)
            vectors = [
                (1, [marker, "localized or garbled message"], target, True),
                (0, [marker], target, False),
                (1, [self.denial_record(existing)], existing, False),
                (1, ["helper_sandbox_lock_failed"], target, False),
                (1, [marker, "windows sandbox failed: helper_error"], target, False),
                (1, ["Access is denied"], target, False),
                (1, [marker.replace("operation=Write", "operation=Read")], target, False),
                (1, [marker.replace("UnauthorizedAccessException", "IOException")], target, False),
                (1, [marker.replace("-2147024891", "-2147024894")], target, False),
                (1, [self.denial_record(root / "other.txt")], target, False),
                (1, [marker, marker], target, False),
                (1, [], target, False),
            ]
            cases_file = root / "cases.json"
            cases_file.write_text(json.dumps([
                {"code": code, "output": output, "path": str(path)}
                for code, output, path, _ in vectors
            ]), encoding="utf-8")
            env = os.environ.copy()
            env["SANDBOX76D_CASES"] = str(cases_file)
            command = (
                '$ErrorActionPreference = "Stop"; '
                'Import-Module ($PSHOME + "\\Modules\\Microsoft.PowerShell.Management\\Microsoft.PowerShell.Management.psd1") -Cmdlet Test-Path; '
                'Import-Module ($PSHOME + "\\Modules\\Microsoft.PowerShell.Utility\\Microsoft.PowerShell.Utility.psd1") -Cmdlet ConvertFrom-Json; '
                + self.denial_function
                + '\n$cases = [IO.File]::ReadAllText($env:SANDBOX76D_CASES) | ConvertFrom-Json; '
                'foreach ($case in $cases) { '
                '$accepted = Test-SandboxWriteDenial -ExitCode $case.code -Output $case.output -LiteralPath $case.path; '
                '[Console]::WriteLine($accepted.ToString()) }; exit 0'
            )
            proc = self.run_query(command, env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(
                proc.stdout.splitlines(), [str(v[-1]) for v in vectors]
            )
            self.assertFalse(target.exists())
            self.assertEqual(existing.read_text(encoding="ascii"), "must remain")

    def test_probe_emits_real_root_exception_without_changing_permissions(self):
        with tempfile.TemporaryDirectory(prefix="probe-76d-") as folder:
            root = Path(folder)
            # Writing onto an existing directory is an actual Windows
            # UnauthorizedAccessException, with no ACL/attribute mutation.
            for path, exception in (
                (root, "System.UnauthorizedAccessException"),
                (root / "missing-parent" / "file.txt", "System.IO.DirectoryNotFoundException"),
            ):
                with self.subTest(exception=exception):
                    proc = subprocess.run(
                        [str(self.shell), "-NoProfile", "-NonInteractive", "-File",
                         str(REPO / "scripts/WindowsSandbox76dProbe.ps1"),
                         "-Operation", "Write", "-LiteralPath", str(path)],
                        capture_output=True, timeout=30, check=False,
                    )
                    error = proc.stderr.decode("utf-8", errors="replace")
                    self.assertEqual(proc.returncode, 1, error)
                    self.assertIn(f"|type={exception}|", error)
                    if exception == "System.UnauthorizedAccessException":
                        self.assertIn(self.denial_record(path), error.splitlines())
                    else:
                        self.assertNotIn(self.denial_record(path), error)
            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
