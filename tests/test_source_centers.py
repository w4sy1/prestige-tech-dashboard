"""Centra w sąsiednim repozytorium można uruchomić bez zbudowanego EXE."""

import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from module_manager import ModuleManager, SOURCE_CENTERS


class SourceCentersTests(unittest.TestCase):
    def setUp(self):
        self.manager = ModuleManager()

    def test_every_source_center_is_in_manifest_and_has_launcher(self):
        modules = {module.id: module for module in self.manager.modules}
        self.assertEqual(len(SOURCE_CENTERS), 10)
        with TemporaryDirectory() as directory:
            source_dir = Path(directory) / "prestige-tech"
            source_dir.mkdir()
            for filename in SOURCE_CENTERS.values():
                (source_dir / filename).touch()
            with patch("module_manager.__file__", str(Path(directory) / "dashboard" / "module_manager.py")):
                for module_id, filename in SOURCE_CENTERS.items():
                    with self.subTest(module_id=module_id):
                        self.assertIn(module_id, modules)
                        self.assertEqual(self.manager.source_path(modules[module_id]).name, filename)

    def test_launch_uses_python_and_source_directory(self):
        module = next(m for m in self.manager.modules if m.id == "prestige-network-center")
        with TemporaryDirectory() as directory:
            source_dir = Path(directory) / "prestige-tech"
            source_dir.mkdir()
            source = source_dir / SOURCE_CENTERS[module.id]
            source.touch()
            with patch("module_manager.__file__", str(Path(directory) / "dashboard" / "module_manager.py")), \
                 patch.object(self.manager, "executable_path", return_value=Path("missing.exe")), \
                 patch("module_manager.subprocess.Popen") as launch:
                self.manager.launch(module)
        args, kwargs = launch.call_args
        self.assertEqual(Path(args[0][1]).resolve(), source.resolve())
        self.assertEqual(kwargs["cwd"].resolve(), source.parent.resolve())

    def test_unknown_module_cannot_launch_arbitrary_source(self):
        module = next(m for m in self.manager.modules if m.id not in SOURCE_CENTERS)
        self.assertIsNone(self.manager.source_path(module))

    def test_security_center_source_and_legacy_file_inspector_stay_separate(self):
        modules = {module.id: module for module in self.manager.modules}
        center = modules["prestige-security-center"]
        legacy = modules["prestige-file-inspector"]
        with TemporaryDirectory() as directory:
            source_dir = Path(directory) / "prestige-tech"
            source_dir.mkdir()
            source = source_dir / "security_center.py"
            source.touch()
            old_exe = Path(directory) / "prestige-file-inspector.exe"
            old_exe.touch()
            with patch("module_manager.__file__", str(Path(directory) / "dashboard" / "module_manager.py")), \
                 patch.object(self.manager, "executable_path", side_effect=lambda m: old_exe if m == legacy else Path(directory) / "missing.exe"), \
                 patch("module_manager.subprocess.Popen") as launch:
                self.manager.launch(center)
                self.assertEqual(Path(launch.call_args.args[0][1]).resolve(), source.resolve())
                self.manager.launch(legacy)
                self.assertEqual(launch.call_args.args[0], [str(old_exe)])


if __name__ == "__main__":
    unittest.main()
