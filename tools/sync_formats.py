#!/usr/bin/env python3
"""
Utility to synchronize OWL and TTL ontology formats.
Ensures both formats contain identical semantic content.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.cli_common import create_base_parser, handle_keyboard_interrupt
from utils.common import (
    TTL_FORMAT,
    XML_FORMAT,
    get_ontology_files,
    load_ontology_graph,
    serialize_rdfxml,
)
from utils.logging_config import setup_tool_logging

try:
    from rdflib import Graph
except ImportError:
    print("rdflib not installed. Install with: pip install rdflib")
    sys.exit(1)


def convert_ttl_to_owl(ttl_file: Path, owl_file: Path) -> bool:
    """Convert TTL file to OWL/XML format."""
    try:
        graph = load_ontology_graph(ttl_file, TTL_FORMAT)
        if graph is None:
            return False

        # Serialize to OWL/XML in a stable order, so the file only changes where the ontology does
        owl_content = serialize_rdfxml(graph)

        # Write to file
        with open(owl_file, "w", encoding="utf-8") as f:
            f.write(owl_content)

        print(f"✅ Converted {ttl_file} → {owl_file}")
        return True

    except Exception as e:
        print(f"❌ Failed to convert TTL to OWL: {e}")
        return False


def convert_owl_to_ttl(owl_file: Path, ttl_file: Path) -> bool:
    """Convert OWL/XML file to TTL format."""
    try:
        graph = load_ontology_graph(owl_file, XML_FORMAT)
        if graph is None:
            return False

        # Serialize to TTL
        ttl_content = graph.serialize(format="turtle")

        # Write to file
        with open(ttl_file, "w", encoding="utf-8") as f:
            if isinstance(ttl_content, bytes):
                f.write(ttl_content.decode("utf-8"))
            else:
                f.write(ttl_content)

        print(f"✅ Converted {owl_file} → {ttl_file}")
        return True

    except Exception as e:
        print(f"❌ Failed to convert OWL to TTL: {e}")
        return False


def check_sync_status(owl_file: Path, ttl_file: Path) -> bool:
    """Check if OWL and TTL files are synchronized."""
    try:
        # Load both files
        owl_graph = Graph()
        owl_graph.parse(str(owl_file), format="xml")

        ttl_graph = Graph()
        ttl_graph.parse(str(ttl_file), format="turtle")

        # Compare sizes
        owl_size = len(owl_graph)
        ttl_size = len(ttl_graph)

        if owl_size != ttl_size:
            print(f"❌ Different number of triples: OWL={owl_size}, TTL={ttl_size}")
            return False

        # Check semantic equivalence
        from rdflib import compare

        if not compare.isomorphic(owl_graph, ttl_graph):
            print("❌ Files are not semantically equivalent")
            return False

        print(f"✅ Files are synchronized ({owl_size} triples each)")
        return True

    except Exception as e:
        print(f"❌ Failed to check synchronization: {e}")
        return False


def sync_formats(direction: str = "ttl_to_owl") -> bool:
    """Synchronize ontology formats."""
    ttl_file, owl_file, _ = get_ontology_files()

    if direction == "ttl_to_owl":
        return convert_ttl_to_owl(ttl_file, owl_file)
    elif direction == "owl_to_ttl":
        return convert_owl_to_ttl(owl_file, ttl_file)
    else:
        print("❌ Invalid direction")
        return False


@handle_keyboard_interrupt
def main():
    """Main function."""
    parser = create_base_parser(
        "sync_formats", "Synchronize OWL and TTL ontology formats", version="0.4.0"
    )

    parser.add_argument(
        "action", choices=["check", "ttl-to-owl", "owl-to-ttl", "sync"], help="Action to perform"
    )

    parser.add_argument(
        "--owl", default="ontology/aws.owl", help="Path to OWL file (default: ontology/aws.owl)"
    )

    args = parser.parse_args()

    # Set up logging
    setup_tool_logging("sync_formats", args.verbose)

    # Resolve paths
    owl_file = Path(args.owl)

    # Validate files exist for relevant operations
    if args.action in ["check", "owl-to-ttl", "sync"]:
        if not owl_file.exists():
            print(f"❌ OWL file not found: {owl_file}")
            sys.exit(1)

    # Execute action
    success = True

    if args.action == "check":
        ttl_file, owl_file, _ = get_ontology_files()
        success = check_sync_status(owl_file, ttl_file)

    elif args.action == "ttl-to-owl":
        ttl_file, owl_file, _ = get_ontology_files()
        success = convert_ttl_to_owl(ttl_file, owl_file)

    elif args.action == "owl-to-ttl":
        ttl_file, owl_file, _ = get_ontology_files()
        success = convert_owl_to_ttl(owl_file, ttl_file)

    elif args.action == "sync":
        # Check if they're already synchronized
        ttl_file, owl_file, _ = get_ontology_files()
        if check_sync_status(owl_file, ttl_file):
            print("Files are already synchronized!")
        else:
            print("Files are out of sync. Choose which file to use as source:")
            print("1. Use TTL as source (convert TTL → OWL)")
            print("2. Use OWL as source (convert OWL → TTL)")

            choice = input("Enter choice (1 or 2): ").strip()

            if choice == "1":
                success = convert_ttl_to_owl(ttl_file, owl_file)
            elif choice == "2":
                success = convert_owl_to_ttl(owl_file, ttl_file)
            else:
                print("❌ Invalid choice")
                success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
