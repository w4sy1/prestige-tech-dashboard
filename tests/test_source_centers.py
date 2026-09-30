"""Centra w sąsiednim repozytorium można uruchomić bez zbudowanego EXE."""

import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from module_manager import Module, ModuleManager, SOURCE_CENTERS


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
        module = Module("unknown", "Unknown", "Other", "0", "", "unknown.exe", (), "safe", "")
        self.assertIsNone(self.manager.source_path(module))

    def test_catalog_contains_only_current_centers(self):
        modules = {module.id: module for module in self.manager.modules}
        self.assertEqual(set(modules), set(SOURCE_CENTERS))
        from ui.home_page import MAIN
        from ui.widgets import CATEGORY_STYLE
        categories = {module.category for module in modules.values()}
        self.assertEqual({name for name, _ in MAIN}, categories)
        self.assertTrue(categories.issubset(CATEGORY_STYLE))


if __name__ == "__main__":
    unittest.main()
