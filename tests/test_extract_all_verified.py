"""Synthetic extract_all tests for numbered-part routing and path safety."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "cf_extract"))
sys.path.insert(0, str(ROOT / "scripts" / "material_recovery"))
sys.path.insert(0, str(ROOT / "tests"))

import extract_all
import rez_synthetic


class ExtractAllVerifiedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.index = self.root / "rf017.rez"
        self.out = self.root / "out"

    def test_main_range_legal_but_wrong_bytes_uses_part(self):
        rez_synthetic.write_rez(self.index, [{
            "full_path": "PLAYERVIEW/gun.dtx",
            "data": b"GOOD",
            "time": 8,
            "offset": 400,
            "in_index": True,
            "write_part": True,
        }])
        # Overwrite the in-index copy after the writer placed GOOD in both.
        blob = bytearray(self.index.read_bytes())
        blob[400:404] = b"BAD!"
        self.index.write_bytes(bytes(blob))
        written = extract_all.extract_archive(str(self.index), str(self.out))
        dest = self.out / "PLAYERVIEW" / "gun.dtx"
        self.assertEqual(dest.read_bytes(), b"GOOD")
        self.assertEqual(written[0]["routing"], "numbered_part")
        self.assertEqual(written[0]["sha256"], hashlib.sha256(b"GOOD").hexdigest())

    def test_payload_beyond_main_file_reads_part(self):
        rez_synthetic.write_rez(self.index, [{
            "full_path": "PLAYERVIEW/gun.dtx",
            "data": b"GOOD",
            "time": 8,
            "offset": 800,
            "in_index": False,
            "write_part": True,
        }])
        self.assertLess(self.index.stat().st_size, 800)
        dest = Path(extract_all.extract_archive(str(self.index), str(self.out))[0]["destination"])
        self.assertEqual(dest.read_bytes(), b"GOOD")

    def test_missing_and_truncated_and_wrong_hash_parts_fail(self):
        rez_synthetic.write_rez(self.index, [{
            "full_path": "PLAYERVIEW/gun.dtx",
            "data": b"GOOD",
            "time": 8,
            "offset": 400,
            "in_index": False,
            "write_part": True,
        }])
        part = self.root / "rf017_8.rez"
        part.write_bytes(b"NOPE")
        with self.assertRaisesRegex(ValueError, "found 0"):
            extract_all.extract_archive(str(self.index), str(self.out))
        part.write_bytes(b"G")
        with self.assertRaisesRegex(ValueError, "found 0"):
            extract_all.extract_archive(str(self.index), str(self.out))
        part.unlink()
        with self.assertRaisesRegex(ValueError, "found 0"):
            extract_all.extract_archive(str(self.index), str(self.out))

    def test_timestamp_stays_on_main_file(self):
        rez_synthetic.write_rez(self.index, [{
            "full_path": "root.dtx",
            "data": b"MAIN",
            "time": 1700000000,
            "offset": 400,
            "in_index": True,
        }])
        written = extract_all.extract_archive(str(self.index), str(self.out))
        self.assertEqual(written[0]["routing"], "main_file")
        self.assertEqual((self.out / "root.dtx").read_bytes(), b"MAIN")

    def test_deep_paths_and_same_basename_are_not_overwritten(self):
        rez_synthetic.write_rez(self.index, [
            {
                "full_path": "PLAYERVIEW/gun.dtx",
                "data": b"PVPV",
                "time": 0,
                "offset": 500,
                "in_index": True,
            },
            {
                "full_path": "WEAPONS/gun.dtx",
                "data": b"QVQV",
                "time": 0,
                "offset": 504,
                "in_index": True,
            },
        ])
        extract_all.extract_archive(str(self.index), str(self.out))
        self.assertEqual((self.out / "PLAYERVIEW" / "gun.dtx").read_bytes(), b"PVPV")
        self.assertEqual((self.out / "WEAPONS" / "gun.dtx").read_bytes(), b"QVQV")

    def test_logical_path_filter_matches_full_parent_suffix(self):
        rez_synthetic.write_rez(self.index, [{
            "full_path": "ModelTextures/PLAYERVIEW/gun.dtx",
            "data": b"GOOD",
            "time": 0,
            "offset": 500,
            "in_index": True,
        }])
        written = extract_all.extract_archive(
            str(self.index), str(self.out), ["PLAYERVIEW/gun.dtx"])
        self.assertEqual(written[0]["logical_path"], "ModelTextures/PLAYERVIEW/gun.dtx")
        self.assertEqual((self.out / "ModelTextures" / "PLAYERVIEW" / "gun.dtx").read_bytes(), b"GOOD")

    def test_duplicate_logical_path_is_an_error(self):
        rez_synthetic.write_rez(self.index, [{
            "full_path": "PLAYERVIEW/gun.dtx",
            "data": b"GOOD",
            "time": 0,
            "offset": 400,
            "in_index": True,
        }])
        with self.assertRaisesRegex(ValueError, "Duplicate logical path"):
            extract_all.unique_entries([
                {"full_path": "PLAYERVIEW/gun.dtx"},
                {"full_path": "playerview/gun.dtx"},
            ])

    def test_discover_skips_numbered_part_files(self):
        rez_synthetic.write_rez(self.index, [{
            "full_path": "PLAYERVIEW/gun.dtx",
            "data": b"GOOD",
            "time": 8,
            "offset": 400,
            "in_index": False,
            "write_part": True,
        }])
        found = extract_all.discover_index_archives(str(self.root))
        self.assertEqual(found, [str(self.index)])


if __name__ == "__main__":
    unittest.main()
