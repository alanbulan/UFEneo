"""接续入口的无素材单元检查；不启动Godot或修改游戏资源。"""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("luna_resume_check", Path(__file__).with_name("check.py"))
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.patch = patch.object(check, "ROOT", self.root)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def reference(self, data):
        (self.root / "sample").write_bytes(data)
        return {"path": "sample", "sha256": hashlib.sha256(data).hexdigest()}

    def test_verified_bytes(self):
        self.assertEqual(check.checked(self.reference(b"verified")), self.root / "sample")

    def test_pointer_is_not_an_image_even_with_matching_sha(self):
        ref = self.reference(b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 100\n")
        with self.assertRaisesRegex(ValueError, "LFS"):
            check.checked(ref)

    def test_missing_file(self):
        with self.assertRaisesRegex(ValueError, "缺文件"):
            check.checked({"path": "missing", "sha256": ""})

    def test_wrong_hash(self):
        ref = self.reference(b"original")
        (self.root / "sample").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "SHA256"):
            check.checked(ref)

    def test_path_must_stay_in_checkout(self):
        with self.assertRaises(ValueError):
            check.checked({"path": "../outside", "sha256": ""})

    def test_sixteen_phase_contract(self):
        self.assertEqual(len(check.EXPECTED), 16)
        self.assertIn(("light3", 5), check.EXPECTED)
        self.assertNotIn(("light1", 5), check.EXPECTED)


class RegistrationTests(unittest.TestCase):
    def test_hurtboxes_follow_whole_frame_alpha(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        import register
        from PIL import Image
        image = Image.new("RGBA", (320, 320))
        image.paste((255, 255, 255, 255), (140, 100, 180, 280))
        self.assertEqual(register.hurtboxes(image), [[-20, 120, 40, 60], [-20, 60, 40, 60], [-20, 0, 40, 60]])

    def test_empty_silhouette_rejected(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        import register
        from PIL import Image
        with self.assertRaises(ValueError):
            register.hurtboxes(Image.new("RGBA", (320, 320)))


if __name__ == "__main__":
    unittest.main()
