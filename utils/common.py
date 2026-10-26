#!/usr/bin/env python3
"""
Common utilities for the AWS Ontology project.
Provides shared functionality to reduce code duplication.
"""

import logging
from pathlib import Path

try:
    from rdflib import Graph, Namespace

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
