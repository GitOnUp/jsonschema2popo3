import unittest

from jsonschema2popo3.unit_tests.common import TestCase
from src.jsonschema2popo3.generator import Generator


class TestGeneration(TestCase):
    def test_large_document(self):
        g = Generator()
        with open(self.resource_file("ytapi_schema.json")) as schema_fp:
            g.load(schema_fp)
        file_path = self.output_file_for_test("py")
        g.write_file(str(file_path))
        self.validate_python(file_path)


if __name__ == '__main__':
    unittest.main()
