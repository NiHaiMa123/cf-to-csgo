"""Regression checks for the N05-A local DTX control discovery path."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "material_recovery"))
import n05a_decoder_provenance_audit as audit


def solid_red_dtx():
    # Standard 164-byte LT2 header plus sixteen 4x4 BC1 red blocks.
    # Kept independent of the audit's synthetic-header writer.
    header = bytearray(164)
    struct.pack_into("<iiHHHHII", header, 0, 0, -5, 16, 16, 1, 0, 8, 0)
    header[26] = 4
    return bytes(header) + struct.pack("<HHI", 0xF800, 0, 0) * 16


class ControlScanTests(unittest.TestCase):
    def test_discovers_full_header_and_rejects_truncated_lookalike(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "data"
            root = data / "rf017" / "ModelTextures"
            root.mkdir(parents=True)
            preview = Path(tmp) / "previews"
            preview.mkdir()
            blob = solid_red_dtx()
            (root / "00_truncated.dtx").write_bytes(blob[:64])
            (root / "01_valid.dtx").write_bytes(blob)
            with patch.object(audit, "DATA", data), patch.object(audit, "PREV", preview):
                result = audit.scan_local_control_dtx()
            self.assertEqual(result["status"], "FOUND")
            self.assertEqual(result["scanned"], 2)
            self.assertEqual(len(result["hits"]), 1)
            hit = result["hits"][0]
            self.assertTrue(hit["path"].endswith("01_valid.dtx"))
            self.assertTrue(hit["python_decode_ok"])
            self.assertEqual(hit["repo_header"]["data_offset"], 164)
            with audit.Image.open(hit["preview"]) as image:
                self.assertEqual(image.size, (16, 16))
                self.assertEqual(image.getpixel((8, 8)), (255, 0, 0, 255))

    def test_reports_negative_for_unsupported_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            root = data / "rf017" / "ModelTextures"
            root.mkdir(parents=True)
            (root / "unsupported.dtx").write_bytes(b"\xff" * 292)
            with patch.object(audit, "DATA", data):
                result = audit.scan_local_control_dtx()
            self.assertEqual(result["status"], "NO_CURRENT_CLIENT_CONTROL")
            self.assertEqual(result["scanned"], 1)
            self.assertEqual(result["hits"], [])


if __name__ == "__main__":
    unittest.main()
