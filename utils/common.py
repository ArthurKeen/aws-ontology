#!/usr/bin/env python3
"""
Common utilities for the AWS Ontology project.
Provides shared functionality to reduce code duplication.
"""

import io
import logging
from pathlib import Path

try:
    from rdflib import RDF, BNode, Graph, Literal, Namespace
    from rdflib.compare import to_canonical_graph
    from rdflib.plugins.serializers.rdfxml import XMLSerializer

    RDFLIB_AVAILABLE = True
except ImportError:
    logging.warning("rdflib not installed. Install with: pip install rdflib")
    RDFLIB_AVAILABLE = False


# Constants
ONTOLOGY_NAMESPACE = "https://w3id.org/arango-solutions/aws-ontology#"
TTL_FORMAT = "turtle"
XML_FORMAT = "xml"
OWL_FORMAT = "xml"


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path: The project root directory path
    """
    return Path(__file__).parent.parent


def check_rdflib_available() -> bool:
    """
    Check if rdflib is available for import.

    Returns:
        bool: True if rdflib is available, False otherwise
    """
    return RDFLIB_AVAILABLE


def load_ontology_graph(file_path: Path, format: str = TTL_FORMAT) -> Graph | None:
    """
    Load an ontology file into an RDF graph.

    Args:
        file_path: Path to the ontology file
        format: RDF format (turtle, xml, etc.)

    Returns:
        Graph object if successful, None if failed
    """
    if not check_rdflib_available():
        return None

    try:
        graph = Graph()
        graph.parse(str(file_path), format=format)
        return graph
    except Exception as e:
        logging.error(f"Failed to load ontology from {file_path}: {e}")
        return None


def _term_sort_key(term) -> tuple[int, str, str, str]:
    """Order URIs, then blank nodes, then literals (by value, datatype, language)."""
    if isinstance(term, Literal):
        return (2, str(term), str(term.datatype or ""), term.language or "")
    return (1 if isinstance(term, BNode) else 0, str(term), "", "")


class _SortedGraph(Graph):
    """A graph that yields subjects and predicate-object pairs in sorted order.

    rdflib's RDF/XML serializer writes triples in store iteration order, which
    depends on Python's per-process hash seed, so the same graph would come out
    differently on every run.
    """

    def subjects(self, predicate=None, object=None, unique=False):
        return iter(sorted(set(super().subjects(predicate, object)), key=_term_sort_key))

    def predicate_objects(self, subject=None, unique=False):
        pairs = set(super().predicate_objects(subject))
        # rdf:type first, so each description opens with what the subject is
        return iter(
            sorted(
                pairs,
                key=lambda po: (po[0] != RDF.type, _term_sort_key(po[0]), _term_sort_key(po[1])),
            )
        )


def serialize_rdfxml(graph: Graph) -> str:
    """
    Serialize a graph to RDF/XML deterministically.

    The same graph always produces the same text, and a small change to the graph
    produces a small diff: blank nodes get labels derived from their content
    (rdflib.compare.to_canonical_graph) instead of random IDs, and subjects and
    their properties are written in sorted order.

    Args:
        graph: The graph to serialize

    Returns:
        The RDF/XML document as a string
    """
    ordered = _SortedGraph()
    for prefix, namespace in graph.namespaces():
        ordered.bind(prefix, namespace, override=True, replace=True)
    for triple in to_canonical_graph(graph):
        ordered.add(triple)

    stream = io.BytesIO()
    XMLSerializer(ordered).serialize(stream, encoding="utf-8")
    return stream.getvalue().decode("utf-8")


def get_ontology_files() -> tuple[Path, Path, Path]:
    """
    Get paths to the main ontology files.

    Returns:
        Tuple of (ttl_file, owl_file, examples_file) paths
    """
    project_root = get_project_root()
    ttl_file = project_root / "ontology" / "aws.ttl"
    owl_file = project_root / "ontology" / "aws.owl"
    examples_file = project_root / "ontology" / "examples.ttl"
    return ttl_file, owl_file, examples_file


def setup_aws_namespace(graph: Graph) -> Namespace:
    """
    Set up the AWS ontology namespace for a graph.

    Args:
        graph: RDF graph to bind namespace to

    Returns:
        AWS namespace object
    """
    aws_ns = Namespace(ONTOLOGY_NAMESPACE)
    graph.bind("aws", aws_ns)
    return aws_ns


def validate_file_exists(file_path: Path, description: str = "File") -> bool:
    """
    Validate that a file exists and is readable.

    Args:
        file_path: Path to validate
        description: Description for error messages

    Returns:
        True if file exists and is readable, False otherwise
    """
    if not file_path.exists():
        logging.error(f"{description} not found: {file_path}")
        return False

    if not file_path.is_file():
        logging.error(f"{description} is not a file: {file_path}")
        return False

    try:
        with open(file_path) as f:
            f.read(1)  # Try to read one character
        return True
    except Exception as e:
        logging.error(f"{description} is not readable: {e}")
        return False
