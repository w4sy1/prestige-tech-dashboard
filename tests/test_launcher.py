from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from launcher import resolve,launch,split_arguments,tools

class LauncherTests(unittest.TestCase):
    def test_catalog(self):self.assertEqual(len(tools()),24)
    def test_unknown(self):
        with self.assertRaises(ValueError):resolve('.','../../bad')
    def test_missing(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):resolve(d,'prestige-hash-checker')
    def test_args_no_shell(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'prestige-hash-checker';path.mkdir();(path/'app.py').touch()
            with patch('launcher.subprocess.run') as run:
                run.return_value.returncode=7;self.assertEqual(launch(d,'prestige-hash-checker',['a; b']),7);self.assertFalse(run.call_args.kwargs['shell'])
    def test_quotes(self):self.assertEqual(split_arguments('--input "two words.json"'),['--input','two words.json'])
