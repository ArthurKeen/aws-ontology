#!/usr/bin/env python3
"""
End-to-end ArangoDB import (PRD REQ-020): ontology + examples load through
tools/import_to_arangodb.py with each ArangoRDF transformation, and the PGT result is
traversable.

Needs a live ArangoDB, so it runs only when ARANGO_TEST_HOST is set (CI provides one as a
service container), e.g.:

    ARANGO_TEST_HOST=http://127.0.0.1:8529 ARANGO_PASSWORD=... pytest tests/test_arangodb_import.py

It creates and drops its own uniquely named databases and never touches existing ones.
"""

import os
import sys
import unittest
import uuid
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

ARANGO_TEST_HOST = os.environ.get("ARANGO_TEST_HOST")


@unittest.skipUnless(ARANGO_TEST_HOST, "ARANGO_TEST_HOST not set (needs a live ArangoDB)")
class TestArangoDBImport(unittest.TestCase):
    """Import into a throwaway database per transformation model."""

    @classmethod
    def setUpClass(cls):
        from arango import ArangoClient

        from tools.import_to_arangodb import load_ontology_data

        cls.password = os.environ.get("ARANGO_PASSWORD", "")
        cls.client = ArangoClient(hosts=ARANGO_TEST_HOST)
        cls.sys_db = cls.client.db("_system", username="root", password=cls.password)
        cls.graph = load_ontology_data(include_examples=True)
        cls.created = []

    @classmethod
    def tearDownClass(cls):
        for name in cls.created:
            if cls.sys_db.has_database(name):
                cls.sys_db.delete_database(name)

    def _import(self, model: str):
        from tools.import_to_arangodb import connect_to_arangodb, import_rdf_data

        name = f"aws_ontology_test_{model}_{uuid.uuid4().hex[:8]}"
        self.created.append(name)
        db = connect_to_arangodb(
            host=ARANGO_TEST_HOST, username="root", password=self.password, db_name=name
        )
        self.assertIsNotNone(db, "Could not connect/create test database")
        self.assertTrue(import_rdf_data(db, self.graph, model=model), f"{model} import failed")
        return db

    def test_pgt_import_is_traversable(self):
        from tools.import_to_arangodb import test_queries

        db = self._import("pgt")
        self.assertTrue(db.has_graph("AWSOntology"))
        self.assertTrue(test_queries(db, model="pgt"))

    def test_rpt_import(self):
        db = self._import("rpt")
        self.assertTrue(db.has_graph("AWSOntology"))

    def test_lpg_import(self):
        db = self._import("lpg")
        self.assertTrue(db.has_graph("AWSOntology"))
        self.assertGreater(db.collection("Node").count(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
