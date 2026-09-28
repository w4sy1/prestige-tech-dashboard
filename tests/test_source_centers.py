"""Centra w sąsiednim repozytorium można uruchomić bez zbudowanego EXE."""

import unittest
from pathlib import Path
from unittest.mock import patch

from module_manager import ModuleManager, SOURCE_CENTERS


class SourceCentersTests(unittest.TestCase):
    def setUp(self):
        self.manager = ModuleManager()

    def test_every_source_center_is_in_manifest_and_has_launcher(self):
        modules = {module.id: module for module in self.manager.modules}
        self.assertEqual(len(SOURCE_CENTERS), 10)
        for module_id, filename in SOURCE_CENTERS.items():
            with self.subTest(module_id=module_id):
                self.assertIn(module_id, modules)
                self.assertEqual(self.manager.source_path(modules[module_id]).name, filename)

    def test_launch_uses_python_and_source_directory(self):
        module = next(m for m in self.manager.modules if m.id == "prestige-network-center")
        source = self.manager.source_path(module)
        self.assertIsNotNone(source)
        with patch.object(self.manager, "executable_path", return_value=Path("missing.exe")), \
             patch("module_manager.subprocess.Popen") as launch:
            self.manager.launch(module)
        args, kwargs = launch.call_args
        self.assertEqual(args[0][1], str(source))
        self.assertEqual(kwargs["cwd"], source.parent)

    def test_unknown_module_cannot_launch_arbitrary_source(self):
        module = next(m for m in self.manager.modules if m.id not in SOURCE_CENTERS)
        self.assertIsNone(self.manager.source_path(module))


if __name__ == "__main__":
    unittest.main()
