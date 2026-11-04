# AWS Ontology Tools

This directory contains utilities for working with the AWS Ontology in various formats and performing quality assurance tasks.

## Format Synchronization: `sync_formats.py`

Maintains synchronization between OWL/XML and Turtle (TTL) formats of the ontology.

### Usage

```bash
# Check if formats are synchronized
python tools/sync_formats.py check

# Convert OWL to TTL
python tools/sync_formats.py owl-to-ttl

# Convert TTL to OWL
python tools/sync_formats.py ttl-to-owl

# Auto-sync (chooses direction based on modification times)
python tools/sync_formats.py sync
```

### Features

- **Bidirectional conversion** between OWL/XML and Turtle formats
- **Semantic equivalence checking** to ensure no data loss
- **Automatic format detection** and validation
- **Integration with Git hooks** for pre-commit validation

## AWS Change Monitoring: `monitor_aws_changes.py`

Monitors AWS service documentation for changes that might affect the ontology.

### Usage

```bash
# Run one-time monitoring check
python tools/monitor_aws_changes.py

# Check specific services
python tools/monitor_aws_changes.py --services ec2,s3,iam

# Save results to file
python tools/monitor_aws_changes.py --output changes.json
```

### Features

- **RSS feed monitoring** for AWS service updates
- **Change detection** and classification
- **Automated reporting** with recommendations
- **Scheduling support** for continuous monitoring

## Graph Database Transformation

The ontology can be transformed into various graph database formats:

### RDF Triplestores
```bash
# Load directly into SPARQL-enabled databases
# Compatible with: Stardog, GraphDB, Virtuoso, Blazegraph
```

### Property Graph Formats
```bash
# Transform to Labeled Property Graph (LPG)
# Transform to Property Graph (PG)
# Custom transformation patterns available
```

## Requirements

```bash
pip install rdflib>=6.0.0
```

## Integration Examples

### Python RDF Processing
```python
import rdflib

# Load the ontology
g = rdflib.Graph()
g.parse("ontology/aws.owl", format="xml")

# Query with SPARQL
results = g.query("""
    SELECT ?class ?label WHERE {
        ?class a owl:Class ;
               rdfs:label ?label .
    }
""")
```

### Format Validation
```python
from tools.sync_formats import check_synchronization

# Validate format consistency
is_synced, details = check_synchronization()
if is_synced:
    print("✅ Formats are synchronized")
else:
    print(f"❌ Sync issues: {details}")
```

## Development Tools

- **Format synchronization** with semantic validation
- **Quality assurance** testing framework
- **Change monitoring** for AWS updates
- **Documentation generation** helpers
- **Git integration** hooks and validators