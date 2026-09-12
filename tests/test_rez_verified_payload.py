import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "material_recovery"))
from rez_verified_payload import read_verified_payload


class VerifiedPayloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name) / "rf017.rez"
        self.base.write_bytes(b"BAD!")
        self.part = Path(self.tmp.name) / "RF017_8.REZ"
        self.part.write_bytes(b"GOOD")
        self.entry = {"full_path": "PLAYERVIEW/example.DTX", "data_offset": 0,
                      "size": 4, "time": 8, "md5": hashlib.md5(b"GOOD").hexdigest()}

    def test_routes_by_verified_hash_even_when_main_range_is_valid(self):
        data, provenance = read_verified_payload(self.base, self.entry)
        self.assertEqual(data, b"GOOD")
        self.assertEqual(provenance["payload_file"], str(self.part))
        self.assertEqual(self.base.read_bytes(), b"BAD!")

    def test_part_range_is_checked_against_part_not_index_file(self):
        self.base.write_bytes(b"x")
        self.assertEqual(read_verified_payload(self.base, self.entry)[0], b"GOOD")

    def test_main_file_with_legacy_timestamp_still_works(self):
        self.base.write_bytes(b"GOOD")
        self.entry["time"] = 1700000000
        self.assertEqual(read_verified_payload(self.base, self.entry)[1]["routing"], "main_file")

    def test_bad_part_does_not_fall_back_to_wrong_main_bytes(self):
        self.part.write_bytes(b"NOPE")
        with self.assertRaisesRegex(ValueError, "found 0"):
            read_verified_payload(self.base, self.entry)

    def test_two_matching_candidates_are_reported_as_ambiguous(self):
        self.base.write_bytes(b"GOOD")
        with self.assertRaisesRegex(ValueError, "found 2"):
            read_verified_payload(self.base, self.entry)


if __name__ == "__main__":
    unittest.main()
