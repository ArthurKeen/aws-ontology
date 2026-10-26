#!/usr/bin/env python3
"""
Performance tests for AWS Ontology.
Tests loading time, query performance, and memory usage.
"""

import sys
import time
import tracemalloc
import unittest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.base_test import BaseOntologyTest

try:
    from rdflib import OWL, RDF, Graph

    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False


@unittest.skipUnless(RDFLIB_AVAILABLE, "rdflib not available")
class TestOntologyPerformance(BaseOntologyTest):
    """Performance tests for the ontology."""

    def test_ttl_loading_performance(self):
        """Test TTL file loading performance."""
        start_time = time.time()

        # Use base class method for consistency
        from utils.common import TTL_FORMAT, load_ontology_graph

        load_ontology_graph(self.ttl_file, TTL_FORMAT)

        load_time = time.time() - start_time

        # Should load within 5 seconds (as per PRD success metrics)
        self.assertLess(load_time, 5.0, f"TTL loading took {load_time:.2f}s, should be < 5s")

        print(f"TTL loading time: {load_time:.3f}s")

    def test_owl_loading_performance(self):
        """Test OWL file loading performance."""
        start_time = time.time()

        graph = Graph()
        graph.parse(str(self.owl_file), format="xml")

        load_time = time.time() - start_time

        # Should load within 5 seconds (as per PRD success metrics)
        self.assertLess(load_time, 5.0, f"OWL loading took {load_time:.2f}s, should be < 5s")

        print(f"OWL loading time: {load_time:.3f}s")

    def test_memory_usage(self):
        """Test memory usage during ontology loading."""
        tracemalloc.start()

        graph = Graph()
        graph.parse(str(self.ttl_file), format="turtle")

        # Load examples too
        graph.parse(str(self.examples_file), format="turtle")

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Convert to MB
        peak_mb = peak / 1024 / 1024

        # Should use less than 500MB (as per PRD success metrics)
        self.assertLess(peak_mb, 500.0, f"Peak memory usage {peak_mb:.1f}MB, should be < 500MB")

        print(f"Peak memory usage: {peak_mb:.1f}MB")

    def test_simple_query_performance(self):
        """Test performance of simple SPARQL queries."""
        # Load ontology
        graph = Graph()
        graph.parse(str(self.ttl_file), format="turtle")

        # Define test queries
        queries = [
            # Count all classes
            """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            SELECT (COUNT(?class) as ?count) WHERE {
                ?class a owl:Class .
            }
            """,
            # Count all properties
            """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            SELECT (COUNT(?prop) as ?count) WHERE {
                { ?prop a owl:ObjectProperty } UNION
                { ?prop a owl:DatatypeProperty }
            }
            """,
            # Find all IAM classes
            """
            PREFIX aws: <https://w3id.org/arango-solutions/aws-ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?class WHERE {
                ?class rdfs:subClassOf* aws:IdentityResource .
            }
            """,
        ]

        for i, query in enumerate(queries):
            start_time = time.time()

            results = list(graph.query(query))

            query_time = time.time() - start_time

            # Should complete within 1 second (as per PRD success metrics)
            self.assertLess(
                query_time, 1.0, f"Query {i + 1} took {query_time:.3f}s, should be < 1s"
            )

            print(f"Query {i + 1} time: {query_time:.3f}s, results: {len(results)}")

    def test_complex_query_performance(self):
        """Test performance of more complex SPARQL queries."""
        # Load ontology and examples
        graph = Graph()
        graph.parse(str(self.ttl_file), format="turtle")
        graph.parse(str(self.examples_file), format="turtle")

        # Complex query: Find all IAM users with their groups and policies
        complex_query = """
        PREFIX aws: <https://w3id.org/arango-solutions/aws-ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?user ?userLabel ?group ?groupLabel ?policy ?policyLabel WHERE {
            ?user a aws:IAMUser ;
                  rdfs:label ?userLabel .
            OPTIONAL {
                ?user aws:memberOf ?group .
                ?group rdfs:label ?groupLabel .
            }
            OPTIONAL {
                ?user aws:hasPolicyAttachment ?policy .
                ?policy rdfs:label ?policyLabel .
            }
        }
        """

        start_time = time.time()

        results = list(graph.query(complex_query))

        query_time = time.time() - start_time

        # Complex queries should still complete reasonably quickly
        self.assertLess(query_time, 2.0, f"Complex query took {query_time:.3f}s, should be < 2s")

        print(f"Complex query time: {query_time:.3f}s, results: {len(results)}")

    def test_graph_size_metrics(self):
        """Test and report graph size metrics."""
        # Load ontology
        graph = Graph()
        graph.parse(str(self.ttl_file), format="turtle")

        triple_count = len(graph)

        # Should have a reasonable number of triples
        self.assertGreater(triple_count, 100, f"Graph has {triple_count} triples, expected > 100")

        print(f"Total triples in ontology: {triple_count}")

        # Count different types of statements
        classes = len(list(graph.subjects(RDF.type, OWL.Class)))
        obj_props = len(list(graph.subjects(RDF.type, OWL.ObjectProperty)))
        data_props = len(list(graph.subjects(RDF.type, OWL.DatatypeProperty)))

        print(f"Classes: {classes}")
        print(f"Object Properties: {obj_props}")
        print(f"Data Properties: {data_props}")

        # Verify we meet PRD expectations
        self.assertGreater(classes, 20, "Should have > 20 classes")
        self.assertGreater(obj_props, 10, "Should have > 10 object properties")
        self.assertGreater(data_props, 5, "Should have > 5 data properties")

    def test_reasoner_performance(self):
        """Test basic reasoning performance (if reasoner available)."""
        try:
            from owlrl import DeductiveClosure, OWLRL_Semantics
        except ImportError:
            self.skipTest("owlrl not available for reasoning tests")
            return

        # Load ontology
        graph = Graph()
        graph.parse(str(self.ttl_file), format="turtle")

        initial_size = len(graph)

        start_time = time.time()

        # Apply OWL RL reasoning
        DeductiveClosure(OWLRL_Semantics).expand(graph)

        reasoning_time = time.time() - start_time
        final_size = len(graph)

        print(f"Reasoning time: {reasoning_time:.3f}s")
        print(f"Triples before reasoning: {initial_size}")
        print(f"Triples after reasoning: {final_size}")
        print(f"Inferred triples: {final_size - initial_size}")

        # Reasoning should complete in reasonable time
        self.assertLess(
            reasoning_time, 10.0, f"Reasoning took {reasoning_time:.3f}s, should be < 10s"
        )


def run_performance_tests():
    """Run all performance tests."""
    if not RDFLIB_AVAILABLE:
        print("❌ rdflib not available. Install with: pip install rdflib")
        return False

    suite = unittest.TestLoader().loadTestsFromTestCase(TestOntologyPerformance)
    runner = unittest.TextTestRunner(verbosity=2, buffer=False)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running ontology performance tests...")
    success = run_performance_tests()

    if success:
        print("\n✅ All performance tests passed!")
        exit(0)
    else:
        print("\n❌ Some performance tests failed!")
        exit(1)
