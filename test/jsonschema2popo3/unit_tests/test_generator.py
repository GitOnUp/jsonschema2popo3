import os
import tempfile
import unittest
from pathlib import Path

from src.jsonschema2popo3.generator import Generator

resource_dir = Path(os.path.dirname(__file__)) / "resource"


class TestGeneration(unittest.TestCase):
    def test_large_document(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            g = Generator()
            with open(str(resource_dir / "ytapi_schema.json")) as schema_fp:
                g.load(schema_fp)
            file_path = Path(tmpdir) / "out.py"
            g.write_file(str(file_path))
            pass


if __name__ == '__main__':
    unittest.main()
