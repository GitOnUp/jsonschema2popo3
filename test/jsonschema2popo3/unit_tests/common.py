import importlib.util
import os
import unittest
import uuid
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Optional

UNIT_TESTS_DIR = Path(os.path.dirname(__file__))
assert UNIT_TESTS_DIR.name == "unit_tests"

OUTPUT_DIR = UNIT_TESTS_DIR / "output"
assert OUTPUT_DIR.exists() and OUTPUT_DIR.is_dir()

RESOURCE_DIR = UNIT_TESTS_DIR / "resource"
assert RESOURCE_DIR.exists() and RESOURCE_DIR.is_dir()


class TestCase(unittest.TestCase):
    @staticmethod
    def resource_file(name: str) -> Path:
        result = Path(RESOURCE_DIR / name)
        assert result.exists(), f"{name} does not exist in unit test resource folder."
        return result

    def output_file_for_test(self, suffix: Optional[str], use_ts=True) -> Path:
        _suffix = f".{suffix.lstrip('.')}" if suffix else ""
        _main_part = f"{self.id()}"
        if use_ts:
            _main_part = f"{_main_part}_{datetime.now().timestamp()}"

        filename = f"{_main_part}{_suffix}"
        return OUTPUT_DIR / filename

    @staticmethod
    def validate_python(path: str | Path, module_name: Optional[str] = None) -> ModuleType:
        if not module_name:
            module_name = f"test_{uuid.uuid4()}"
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
