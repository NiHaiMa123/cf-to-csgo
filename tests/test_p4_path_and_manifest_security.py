# -*- coding: utf-8 -*-
"""Automated tests for P4-T02 Manifest Contract and Path Security.

Tests all negative mutations, schema validation rules, boundary constraints,
and sandboxed execution requirements. Uses temp directories and never touches real game/MIGI files.
"""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from weapon_port.validate_manifest_contract import (
    validate_manifest_contract,
    validate_output_path,
    is_path_contained,
    ALLOWED_BUILD_SUBTREE,
    ALLOWED_WORK_SUBTREE,
)

MANIFEST_ORIGINAL = PROJECT_ROOT / "assets" / "weapons" / "m4a1_s_bornbeast" / "prototype_01_manifest.json"


class TestP4ManifestContractAndPathSecurity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        with MANIFEST_ORIGINAL.open("r", encoding="utf-8") as f:
            self.base_manifest = json.load(f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_temp_manifest(self, manifest_data: dict) -> Path:
        p = self.temp_path / "temp_manifest.json"
        p.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return p

    def test_01_valid_baseline_manifest_passes(self):
        """Original prototype_01_manifest.json must pass all contract checks."""
        passed, report = validate_manifest_contract(MANIFEST_ORIGINAL)
        self.assertTrue(passed, f"Baseline manifest failed with errors: {report.get('errors')}")
        self.assertEqual(len(report["errors"]), 0)
        self.assertTrue(report["pass"])
        self.assertIn("field_consumption_matrix", report)

    def test_02_missing_required_fields_fails(self):
        """Missing top-level required fields must fail."""
        for required_field in ("schema", "profile_id", "runtime", "inputs", "toolchain", "outputs", "material_policy"):
            mutated = copy.deepcopy(self.base_manifest)
            del mutated[required_field]
            mp = self._write_temp_manifest(mutated)
            passed, report = validate_manifest_contract(mp)
            self.assertFalse(passed, f"Expected failure when missing '{required_field}', but passed.")
            self.assertGreater(len(report["errors"]), 0)

    def test_03_unrecognized_top_level_field_fails(self):
        """Unrecognized fields must raise error, not be silently ignored."""
        mutated = copy.deepcopy(self.base_manifest)
        mutated["unknown_field_123"] = "dangerous_value"
        mp = self._write_temp_manifest(mutated)
        passed, report = validate_manifest_contract(mp)
        self.assertFalse(passed)
        self.assertTrue(any("unrecognized top-level fields" in err for err in report["errors"]))

    def test_04_input_missing_role_or_hash_fails(self):
        """Each input must have path, sha256, and role."""
        # Missing role
        mutated = copy.deepcopy(self.base_manifest)
        del mutated["inputs"]["cf_ltb_source"]["role"]
        mp = self._write_temp_manifest(mutated)
        passed, report = validate_manifest_contract(mp)
        self.assertFalse(passed)
        self.assertTrue(any("missing valid 'role'" in err for err in report["errors"]))

        # Invalid sha256
        mutated2 = copy.deepcopy(self.base_manifest)
        mutated2["inputs"]["cf_ltb_source"]["sha256"] = "invalid_short_hash"
        mp2 = self._write_temp_manifest(mutated2)
        passed2, report2 = validate_manifest_contract(mp2)
        self.assertFalse(passed2)

    def test_05_input_hash_mismatch_fails(self):
        """Input with wrong sha256 hash must fail."""
        mutated = copy.deepcopy(self.base_manifest)
        mutated["inputs"]["cf_ltb_source"]["sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
        mp = self._write_temp_manifest(mutated)
        passed, report = validate_manifest_contract(mp)
        self.assertFalse(passed)
        self.assertTrue(any("Input hash mismatch" in err for err in report["errors"]))

    def test_06_final_flags_in_p4_fail(self):
        """P4 strictly rejects final_target_identity=true or final_cf_material=true."""
        mutated = copy.deepcopy(self.base_manifest)
        mutated["final_target_identity"] = True
        mp = self._write_temp_manifest(mutated)
        passed, report = validate_manifest_contract(mp)
        self.assertFalse(passed)

        mutated2 = copy.deepcopy(self.base_manifest)
        mutated2["final_cf_material"] = True
        mp2 = self._write_temp_manifest(mutated2)
        passed2, report2 = validate_manifest_contract(mp2)
        self.assertFalse(passed2)

    def test_07_invalid_material_policy_fails(self):
        """Classification other than EXTERNAL_REFERENCE / PROTOTYPE MATERIAL must fail."""
        mutated = copy.deepcopy(self.base_manifest)
        mutated["material_policy"]["classification"] = "OFFICIAL_CF_LOCAL_CANONICAL_MATERIAL"
        mp = self._write_temp_manifest(mutated)
        passed, report = validate_manifest_contract(mp)
        self.assertFalse(passed)

    def test_08_runtime_slot_and_modelname_constraints(self):
        """Runtime must strictly be m4a4 and weapons/v_rif_m4a1.mdl."""
        mutated = copy.deepcopy(self.base_manifest)
        mutated["runtime"]["slot"] = "ak47"
        mp = self._write_temp_manifest(mutated)
        passed, report = validate_manifest_contract(mp)
        self.assertFalse(passed)

        mutated2 = copy.deepcopy(self.base_manifest)
        mutated2["runtime"]["modelname"] = "weapons/v_rif_ak47.mdl"
        mp2 = self._write_temp_manifest(mutated2)
        passed2, report2 = validate_manifest_contract(mp2)
        self.assertFalse(passed2)

    def test_09_absolute_output_path_fails(self):
        """Absolute output paths must be rejected."""
        mutated = copy.deepcopy(self.base_manifest)
        mutated["outputs"]["build_root"] = "C:/Windows/System32" if os.name == "nt" else "/tmp/root"
        mp = self._write_temp_manifest(mutated)
        passed, report = validate_manifest_contract(mp)
        self.assertFalse(passed)
        self.assertTrue(any("must be a relative path" in err for err in report["errors"]))

    def test_10_parent_traversal_output_path_fails(self):
        """Output paths with .. traversal must be rejected."""
        mutated = copy.deepcopy(self.base_manifest)
        mutated["outputs"]["build_root"] = "work/m4a1_s_bornbeast/p4_prototype_01/../../escape"
        mp = self._write_temp_manifest(mutated)
        passed, report = validate_manifest_contract(mp)
        self.assertFalse(passed)
        self.assertTrue(any("parent traversal '..'" in err for err in report["errors"]))

    def test_11_output_pointing_to_repo_or_work_root_fails(self):
        """Output paths pointing to repository root, build root, or work root must be rejected."""
        for bad_out in (".", "build", "work", "work/m4a1_s_bornbeast"):
            mutated = copy.deepcopy(self.base_manifest)
            mutated["outputs"]["build_root"] = bad_out
            mp = self._write_temp_manifest(mutated)
            passed, report = validate_manifest_contract(mp)
            self.assertFalse(passed, f"Expected output path '{bad_out}' to be rejected.")

    def test_12_pipeline_cli_check_returns_nonzero_on_invalid_manifest(self):
        """pipeline.py check must exit non-zero when given an invalid manifest."""
        mutated = copy.deepcopy(self.base_manifest)
        mutated["final_target_identity"] = True  # Violates P4 gate
        mp = self._write_temp_manifest(mutated)

        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "weapon_port" / "pipeline.py"), "check", "--manifest", str(mp)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_13_pipeline_cli_deploy_requires_migi_addon(self):
        """pipeline.py deploy without --migi-addon must exit non-zero."""
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "weapon_port" / "pipeline.py"), "deploy", "--manifest", str(MANIFEST_ORIGINAL)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env={**os.environ, "CF2_GAME_DIR": str(self.temp_path / "game")},
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Deploy requires explicit --migi-addon", proc.stdout + proc.stderr)

    def test_14_pipeline_cli_deploy_refuses_different_content_overwrite(self):
        """pipeline.py deploy must refuse to overwrite an existing directory with differing contents."""
        # Create a mock MIGI addons directory in temp
        fake_migi_addons = self.temp_path / "migi" / "csgo" / "addons"
        target_addon = fake_migi_addons / "test_addon_differing"
        target_addon.mkdir(parents=True, exist_ok=True)
        (target_addon / "dummy.txt").write_text("different_content_123", encoding="utf-8")

        # Calling deploy pointing to this differing directory should fail
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "weapon_port" / "pipeline.py"),
                "deploy",
                "--manifest", str(MANIFEST_ORIGINAL),
                "--migi-addon", str(target_addon),
                "--allow-custom-deploy-path",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env={**os.environ, "CF2_GAME_DIR": str(self.temp_path / "game")},
        )
        self.assertNotEqual(proc.returncode, 0)
        # Dummy file must not be modified or deleted
        self.assertTrue((target_addon / "dummy.txt").is_file())
        self.assertEqual((target_addon / "dummy.txt").read_text(encoding="utf-8"), "different_content_123")

    def test_15_nested_unknown_fields_and_bad_mesh_mapping_fail(self):
        """Nested schema mutations must not be silently accepted."""
        mutations = []
        mutated = copy.deepcopy(self.base_manifest)
        mutated["expectations"]["aligned_obj"]["unknown_nested_field"] = 123
        mutations.append(mutated)

        mutated = copy.deepcopy(self.base_manifest)
        mutated["toolchain"]["d3_builder"].pop("sha256")
        mutated["toolchain"]["d3_builder"].pop("version", None)
        mutations.append(mutated)

        mutated = copy.deepcopy(self.base_manifest)
        mutated["mesh_bone_mapping"][0]["bone_index"] = "not-an-int"
        mutated["mesh_bone_mapping"][0]["expected_triangles"] = -7
        mutated["mesh_bone_mapping"][1]["group"] = mutated["mesh_bone_mapping"][0]["group"]
        mutations.append(mutated)

        for data in mutations:
            mp = self._write_temp_manifest(data)
            passed, report = validate_manifest_contract(mp)
            self.assertFalse(passed, report["errors"])

    def test_16_destructive_output_roots_fail(self):
        """Destructive package roots must be strict descendants, never the P4 work root."""
        for key in ("staging_root", "package_root", "check_report"):
            mutated = copy.deepcopy(self.base_manifest)
            mutated["outputs"][key] = "work/m4a1_s_bornbeast/p4_prototype_01"
            mp = self._write_temp_manifest(mutated)
            passed, report = validate_manifest_contract(mp)
            self.assertFalse(passed, f"Expected destructive root '{key}' to fail: {report['errors']}")

    def test_17_validator_output_override_is_sandboxed(self):
        """Standalone validator must not write reports to an absolute external path."""
        unsafe_output = self.temp_path / "unsafe_report.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "weapon_port" / "validate_manifest_contract.py"),
                "--manifest", str(MANIFEST_ORIGINAL),
                "--output", str(unsafe_output),
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(unsafe_output.exists())

    def test_18_deploy_rejects_dotdot_before_packaging(self):
        """Ordinary deploy must reject '.'/'..' names before package work begins."""
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "weapon_port" / "pipeline.py"),
                "deploy",
                "--manifest", str(MANIFEST_ORIGINAL),
                "--migi-addon", "..",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("safe directory name", proc.stdout + proc.stderr)

    def test_19_symlink_output_escape_fails(self):
        """A resolved symlink/junction path outside the P4 subtree must fail."""
        outside = self.temp_path / "outside"
        outside.mkdir()
        link = ALLOWED_WORK_SUBTREE / "t02_symlink_escape"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        self.addCleanup(lambda: link.unlink(missing_ok=True))
        mutated = copy.deepcopy(self.base_manifest)
        mutated["outputs"]["check_report"] = "work/m4a1_s_bornbeast/p4_prototype_01/t02_symlink_escape/report.json"
        mp = self._write_temp_manifest(mutated)
        passed, report = validate_manifest_contract(mp)
        self.assertFalse(passed, report["errors"])


if __name__ == "__main__":
    unittest.main()
