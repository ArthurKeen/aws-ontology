#!/usr/bin/env python3
"""
Import AWS Ontology into ArangoDB using ArangoRDF.

Supports ArangoRDF's three transformations (see https://github.com/ArangoDB-Community/ArangoRDF):
  pgt  Property Graph Transformation (default): one collection per RDF class
       (e.g. EC2Instance), one edge collection per object property (e.g. belongsToVPC)
  rpt  RDF-topology Preserving Transformation: generic resource/literal/statement collections
  lpg  Labeled Property Graph: a single Node collection and a single Edge collection
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.common import TTL_FORMAT, get_ontology_files, load_ontology_graph
from utils.logging_config import setup_tool_logging

try:
    from arango import ArangoClient
    from arango_rdf import ArangoRDF
    from rdflib import Graph

    ARANGO_AVAILABLE = True
except ImportError as e:
    logging.error(f"ArangoDB dependencies not available: {e}")
    logging.info("Please install: pip install python-arango arango-rdf")
    ARANGO_AVAILABLE = False


def connect_to_arangodb(
    host: str = "http://localhost:8529",
    username: str = "root",
    password: str = None,
    db_name: str = "aws_ontology",
) -> object | None:
    """Connect to ArangoDB and create/access database."""
    if password is None:
        password = os.getenv("ARANGO_PASSWORD")
    if not password:
        logging.error(
            "No ArangoDB password provided. Set the ARANGO_PASSWORD "
            "environment variable or pass --password."
        )
        return None

    try:
        logging.info(f"Connecting to ArangoDB at {host}...")
        client = ArangoClient(hosts=host)

        # Connect to system database first
        sys_db = client.db("_system", username=username, password=password)

        if sys_db.has_database(db_name):
            logging.info(f"Connected to existing database: {db_name}")
        else:
            sys_db.create_database(db_name)
            logging.info(f"Created new database: {db_name}")

        return client.db(db_name, username=username, password=password)

    except Exception as e:
        logging.error(f"Failed to connect to ArangoDB: {e}")
        logging.info("Make sure ArangoDB is running and credentials are correct")
        return None


def load_ontology_data(include_examples: bool = True) -> Graph | None:
    """Load AWS ontology data."""
    logging.info("Loading AWS ontology...")

    ttl_file, owl_file, examples_file = get_ontology_files()

    # Load main ontology
    ontology_graph = load_ontology_graph(ttl_file, TTL_FORMAT)
    if ontology_graph is None:
        logging.error("Failed to load main ontology")
        return None

    logging.info(f"Loaded ontology: {len(ontology_graph)} triples")

    if include_examples:
        # Load examples
        examples_graph = load_ontology_graph(examples_file, TTL_FORMAT)
        if examples_graph is None:
            logging.error("Failed to load examples")
            return None

        logging.info(f"Loaded examples: {len(examples_graph)} triples")

        # Combine ontology and examples
        combined_graph = Graph()
        combined_graph += ontology_graph
        combined_graph += examples_graph

        logging.info(f"Combined total: {len(combined_graph)} triples")
        return combined_graph

    return ontology_graph


TRANSFORMS = {
    "pgt": "rdf_to_arangodb_by_pgt",
    "rpt": "rdf_to_arangodb_by_rpt",
    "lpg": "rdf_to_arangodb_by_lpg",
}


def import_rdf_data(
    db, graph: Graph, model: str = "pgt", graph_name: str = "AWSOntology", overwrite: bool = True
) -> bool:
    """Import RDF data into ArangoDB as a named graph using the chosen ArangoRDF transform."""
    try:
        logging.info("Initializing ArangoRDF...")
        arango_rdf = ArangoRDF(db)

        logging.info(f"Importing {len(graph)} triples into graph '{graph_name}' ({model})...")
        # LPG forwards overwrite_graph to PGT through its **pgt_kwargs.
        transform = getattr(arango_rdf, TRANSFORMS[model])
        transform(graph_name, graph, overwrite_graph=overwrite)

        logging.info("Successfully imported RDF data")
        return True

    except Exception as e:
        logging.error(f"Failed to import RDF data: {e}")
        return False


def print_database_stats(db):
    """Print database statistics."""
    logging.info("Database Statistics:")
    try:
        collections = db.collections()
        total_docs = 0

        for collection in collections:
            if not collection["name"].startswith("_"):
                count = db.collection(collection["name"]).count()
                total_docs += count
                logging.info(f"  {collection['name']}: {count:,} documents")

        logging.info(f"Total documents: {total_docs:,}")

    except Exception as e:
        logging.error(f"Failed to get statistics: {e}")


def test_queries(db, model: str = "pgt") -> bool:
    """Run sanity queries against a PGT import to verify the graph is traversable."""
    if model != "pgt":
        logging.info(f"Test queries are written for the pgt model; skipping for {model}")
        return True

    logging.info("Running test queries...")
    try:
        counts = {}
        for name in ("Class", "EC2Instance", "belongsToVPC"):
            counts[name] = db.collection(name).count() if db.has_collection(name) else 0
            logging.info(f"  {name}: {counts[name]} documents")

        aql = """
        FOR instance IN EC2Instance
            FOR vpc IN 1..1 OUTBOUND instance belongsToVPC
                RETURN {instance: instance._label, vpc: vpc._label}
        """
        placements = list(db.aql.execute(aql))
        logging.info(f"  EC2 instance -> VPC placements: {placements}")

        ok = counts["Class"] > 0 and counts["EC2Instance"] > 0 and bool(placements)
        if not ok:
            logging.error("Test queries found an empty or untraversable graph")
        return ok

    except Exception as e:
        logging.error(f"Test queries failed: {e}")
        return False


def main():
    """Main function."""
    if not ARANGO_AVAILABLE:
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Import AWS Ontology into ArangoDB using ArangoRDF"
    )

    parser.add_argument(
        "--host",
        default=os.getenv("ARANGO_HOST", "http://localhost:8529"),
        help="ArangoDB host (default: $ARANGO_HOST or http://localhost:8529)",
    )

    parser.add_argument(
        "--username",
        default=os.getenv("ARANGO_USERNAME", "root"),
        help="ArangoDB username (default: $ARANGO_USERNAME or root)",
    )

    parser.add_argument(
        "--password", default=None, help="ArangoDB password (default: from ARANGO_PASSWORD env var)"
    )

    parser.add_argument(
        "--database",
        default=os.getenv("ARANGO_DATABASE", "aws_ontology"),
        help="Database name (default: $ARANGO_DATABASE or aws_ontology)",
    )

    parser.add_argument(
        "--model",
        choices=sorted(TRANSFORMS),
        default="pgt",
        help="ArangoRDF transformation: pgt (default), rpt, or lpg",
    )

    parser.add_argument(
        "--graph-name", default="AWSOntology", help="Named graph to create (default: AWSOntology)"
    )

    parser.add_argument(
        "--no-examples", action="store_true", help="Import only ontology, skip examples"
    )

    parser.add_argument(
        "--no-overwrite", action="store_true", help="Do not overwrite existing data"
    )

    parser.add_argument("--test-queries", action="store_true", help="Run test queries after import")

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set up logging
    logger = setup_tool_logging(
        "import_to_arangodb", args.verbose if hasattr(args, "verbose") else False
    )

    logger.info("AWS Ontology → ArangoDB Import Tool")
    logger.info("=" * 50)

    # Step 1: Load ontology data
    graph = load_ontology_data(include_examples=not args.no_examples)
    if graph is None:
        sys.exit(1)

    # Step 2: Connect to ArangoDB
    db = connect_to_arangodb(
        host=args.host, username=args.username, password=args.password, db_name=args.database
    )
    if db is None:
        sys.exit(1)

    # Step 3: Import data
    success = import_rdf_data(
        db, graph, model=args.model, graph_name=args.graph_name, overwrite=not args.no_overwrite
    )
    if not success:
        sys.exit(1)

    # Step 4: Show statistics
    print_database_stats(db)

    # Step 5: Run test queries if requested
    if args.test_queries and not test_queries(db, model=args.model):
        sys.exit(1)

    logger.info("Import completed successfully!")
    logger.info("Next steps:")
    logger.info(f"1. Access ArangoDB web interface: {args.host}")
    logger.info(f"2. Explore database: {args.database}")
    logger.info("3. Run AQL queries on the imported ontology")
    logger.info("4. See docs/ARANGODB_INTEGRATION.md for query examples")


if __name__ == "__main__":
    main()
