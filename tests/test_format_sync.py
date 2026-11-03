#!/usr/bin/env python3
"""
Test script to ensure OWL and TTL ontology files are semantically synchronized.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import difflib
import os
import subprocess
import tempfile

from tests.base_test import BaseOntologyTest
from utils.common import serialize_rdfxml

try:
    from rdflib import OWL, RDF, RDFS, BNode, Graph, Literal, URIRef, compare
except ImportError:
    print("rdflib not installed. Install with: pip install rdflib")
    sys.exit(1)


class TestFormatSynchronization(BaseOntologyTest):
    """Test that OWL and TTL files contain identical semantic content."""

    def setUp(self):
        """Set up test paths."""
        super().setUp()
        # Files are already available from base class

    def test_files_exist(self):
        """Test that both ontology files exist."""
        self.assertTrue(self.owl_file.exists(), f"OWL file not found: {self.owl_file}")
        self.assertTrue(self.ttl_file.exists(), f"TTL file not found: {self.ttl_file}")

    def test_files_parseable(self):
        """Test that both files can be parsed as valid RDF."""
        # Test OWL file
        owl_graph = Graph()
        try:
            owl_graph.parse(str(self.owl_file), format="xml")
        except Exception as e:
            self.fail(f"Failed to parse OWL file: {e}")

        # Test TTL file
        ttl_graph = Graph()
        try:
            ttl_graph.parse(str(self.ttl_file), format="turtle")
        except Exception as e:
            self.fail(f"Failed to parse TTL file: {e}")

    def test_semantic_equivalence(self):
        """Test that OWL and TTL files are semantically equivalent."""
        # Load both graphs
        owl_graph = Graph()
        owl_graph.parse(str(self.owl_file), format="xml")

        ttl_graph = Graph()
        ttl_graph.parse(str(self.ttl_file), format="turtle")

        # Compare graph sizes
        owl_size = len(owl_graph)
        ttl_size = len(ttl_graph)

        self.assertEqual(
            owl_size, ttl_size, f"Different number of triples: OWL={owl_size}, TTL={ttl_size}"
        )

        # Test semantic equivalence using graph isomorphism
        iso_result = compare.isomorphic(owl_graph, ttl_graph)

        if not iso_result:
            # If not isomorphic, find differences for debugging
            owl_only = owl_graph - ttl_graph
            ttl_only = ttl_graph - owl_graph

            error_msg = "Graphs are not semantically equivalent.\n"
            if len(owl_only) > 0:
                error_msg += f"Triples only in OWL ({len(owl_only)}):\n"
                for triple in list(owl_only)[:5]:  # Show first 5
                    error_msg += f"  {triple}\n"
                if len(owl_only) > 5:
                    error_msg += f"  ... and {len(owl_only) - 5} more\n"

            if len(ttl_only) > 0:
                error_msg += f"Triples only in TTL ({len(ttl_only)}):\n"
                for triple in list(ttl_only)[:5]:  # Show first 5
                    error_msg += f"  {triple}\n"
                if len(ttl_only) > 5:
                    error_msg += f"  ... and {len(ttl_only) - 5} more\n"

            self.fail(error_msg)

    def test_owl_file_is_generated_from_ttl(self):
        """The committed OWL file must be exactly what sync_formats.py writes from the TTL."""
        ttl_graph = Graph()
        ttl_graph.parse(str(self.ttl_file), format="turtle")

        expected = serialize_rdfxml(ttl_graph)
        actual = self.owl_file.read_text(encoding="utf-8")

        self.assertTrue(
            actual == expected,
            "aws.owl differs from the deterministic serialization of aws.ttl. "
            "Regenerate it with: python tools/sync_formats.py ttl-to-owl",
        )

    def serialize_in_fresh_process(self, ttl_path: Path, hash_seed: str) -> str:
        """Serialize a TTL file the way sync_formats.py does, in a new Python process."""
        script = (
            "import sys; sys.path.insert(0, '.'); from rdflib import Graph; "
            "from utils.common import serialize_rdfxml; "
            "sys.stdout.write(serialize_rdfxml(Graph().parse(sys.argv[1])))"
        )
        result = subprocess.run(
            [sys.executable, "-c", script, str(ttl_path)],
            capture_output=True,
            text=True,
            cwd=project_root,
            env={**os.environ, "PYTHONHASHSEED": hash_seed},
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_serialization_ignores_hash_seed(self):
        """RDF/XML output must not depend on Python's per-process hash seed."""
        first = self.serialize_in_fresh_process(self.ttl_file, "1")
        second = self.serialize_in_fresh_process(self.ttl_file, "2")

        self.assertTrue(first == second, "RDF/XML output changed with the hash seed")

    def test_small_change_gives_small_diff(self):
        """Adding one class with a restriction must only add lines, not reorder the file."""
        graph = Graph()
        graph.parse(str(self.ttl_file), format="turtle")
        new_class = URIRef("https://w3id.org/arango-solutions/aws-ontology#DiffTestClass")
        restriction = BNode()
        graph.add((new_class, RDF.type, OWL.Class))
        graph.add((new_class, RDFS.label, Literal("Diff Test Class")))
        graph.add((new_class, RDFS.subClassOf, restriction))
        graph.add((restriction, RDF.type, OWL.Restriction))
        graph.add((restriction, OWL.onProperty, RDFS.label))
        graph.add((restriction, OWL.maxCardinality, Literal(1)))

        with tempfile.TemporaryDirectory() as tmp:
            changed_ttl = Path(tmp) / "changed.ttl"
            graph.serialize(destination=str(changed_ttl), format="turtle")
            # Separate runs, as when a contributor regenerates the file after an edit
            before = self.serialize_in_fresh_process(self.ttl_file, "1").splitlines()
            after = self.serialize_in_fresh_process(changed_ttl, "2").splitlines()

        changed = [
            line
            for line in difflib.unified_diff(before, after, lineterm="", n=0)
            if line[:1] in "+-" and not line.startswith(("+++", "---"))
        ]
        removed = [line for line in changed if line.startswith("-")]

        self.assertEqual(removed, [], "Adding triples removed or reordered existing lines")
        self.assertLessEqual(len(changed), 15, f"Expected a small diff, got {len(changed)} lines")

    def test_version_consistency(self):
        """Test that version information is consistent between files."""
        owl_graph = Graph()
        owl_graph.parse(str(self.owl_file), format="xml")

        ttl_graph = Graph()
        ttl_graph.parse(str(self.ttl_file), format="turtle")

        # Query for version information
        version_query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?version WHERE {
            ?ontology a owl:Ontology ;
                      owl:versionInfo ?version .
        }
        """

        owl_versions = list(owl_graph.query(version_query))
        ttl_versions = list(ttl_graph.query(version_query))

        self.assertEqual(
            len(owl_versions),
            1,
            f"Expected exactly one version in OWL file, found {len(owl_versions)}",
        )
        self.assertEqual(
            len(ttl_versions),
            1,
            f"Expected exactly one version in TTL file, found {len(ttl_versions)}",
        )

        owl_version = str(owl_versions[0][0])
        ttl_version = str(ttl_versions[0][0])

        self.assertEqual(
            owl_version, ttl_version, f"Version mismatch: OWL={owl_version}, TTL={ttl_version}"
        )

    def test_class_count_consistency(self):
        """Test that both files have the same number of classes."""
        owl_graph = Graph()
        owl_graph.parse(str(self.owl_file), format="xml")

        ttl_graph = Graph()
        ttl_graph.parse(str(self.ttl_file), format="turtle")

        class_query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(?class) as ?count) WHERE {
            ?class a owl:Class .
        }
        """

        owl_count = int(list(owl_graph.query(class_query))[0][0])
        ttl_count = int(list(ttl_graph.query(class_query))[0][0])

        self.assertEqual(
            owl_count, ttl_count, f"Different number of classes: OWL={owl_count}, TTL={ttl_count}"
        )

        # Ensure we have a reasonable number of classes
        self.assertGreater(owl_count, 20, f"Expected more than 20 classes, found {owl_count}")

    def test_property_count_consistency(self):
        """Test that both files have the same number of properties."""
        owl_graph = Graph()
        owl_graph.parse(str(self.owl_file), format="xml")

        ttl_graph = Graph()
        ttl_graph.parse(str(self.ttl_file), format="turtle")

        object_prop_query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(?prop) as ?count) WHERE {
            ?prop a owl:ObjectProperty .
        }
        """

        data_prop_query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT (COUNT(?prop) as ?count) WHERE {
            ?prop a owl:DatatypeProperty .
        }
        """

        # Object properties
        owl_obj_count = int(list(owl_graph.query(object_prop_query))[0][0])
        ttl_obj_count = int(list(ttl_graph.query(object_prop_query))[0][0])

        self.assertEqual(
            owl_obj_count,
            ttl_obj_count,
            f"Different number of object properties: OWL={owl_obj_count}, TTL={ttl_obj_count}",
        )

        # Data properties
        owl_data_count = int(list(owl_graph.query(data_prop_query))[0][0])
        ttl_data_count = int(list(ttl_graph.query(data_prop_query))[0][0])

        self.assertEqual(
            owl_data_count,
            ttl_data_count,
            f"Different number of data properties: OWL={owl_data_count}, TTL={ttl_data_count}",
        )


def run_sync_test():
    """Run the synchronization test and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFormatSynchronization)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Testing OWL and TTL format synchronization...")
    success = run_sync_test()

    if success:
        print("\n✅ All synchronization tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Synchronization tests failed!")
        sys.exit(1)
