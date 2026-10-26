# ArangoDB Integration Guide

The AWS Ontology (and its example instances) can be loaded into [ArangoDB](https://arango.ai)
with [ArangoRDF](https://github.com/ArangoDB-Community/ArangoRDF) using
`tools/import_to_arangodb.py`. The import is exercised end-to-end in CI against a live
ArangoDB (`tests/test_arangodb_import.py`).

## 1. Start ArangoDB

Any ArangoDB 3.12+ deployment works: Docker, a self-managed cluster, or the Arango managed
platform. For local experiments:

```bash
export ARANGO_PASSWORD='choose-a-strong-password'

docker run -d --name arangodb \
  -e ARANGO_ROOT_PASSWORD="$ARANGO_PASSWORD" \
  -p 127.0.0.1:8529:8529 \
  arangodb:3.12

curl -s -u root:"$ARANGO_PASSWORD" http://localhost:8529/_api/version
```

The web UI is then at <http://localhost:8529>. Credentials are always read from the
`ARANGO_PASSWORD` environment variable (or `--password`); the tools have no built-in default
password. See [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md).

## 2. Import

```bash
uv sync    # or: pip install -r requirements.txt

# Ontology + examples as a Property Graph (default), then run sanity queries
python tools/import_to_arangodb.py --database aws_ontology --test-queries

# Other options
python tools/import_to_arangodb.py --model rpt          # RDF-topology preserving
python tools/import_to_arangodb.py --model lpg          # single Node / Edge collections
python tools/import_to_arangodb.py --no-examples        # T-Box (schema) only
python tools/import_to_arangodb.py --graph-name MyGraph --host https://my-arango:8529
```

The tool creates the database if needed and imports into a named graph (default
`AWSOntology`). Re-running overwrites that graph unless `--no-overwrite` is given.

> **Tip:** ArangoRDF names collections after RDF classes and properties (`Class`, `Property`,
> `type`, `subClassOf`, `EC2Instance`, ...). Import into a dedicated database rather than one
> shared with an application, so these generic names cannot collide with existing collections.

## 3. Choosing a transformation

| `--model` | ArangoRDF method | Shape in ArangoDB | Best for |
|---|---|---|---|
| `pgt` (default) | `rdf_to_arangodb_by_pgt` | One document collection per RDF class (`EC2Instance`, `VPC`, ...), one edge collection per object property (`belongsToVPC`, `attachedTo`, ...); datatype properties become document attributes | Graph analytics and AQL traversals over AWS resources |
| `rpt` | `rdf_to_arangodb_by_rpt` | Generic resource / literal collections and a `Statement` edge collection — every triple preserved | Lossless round-tripping back to RDF |
| `lpg` | `rdf_to_arangodb_by_lpg` | A single `Node` collection and a single `Edge` collection | Tools that expect one vertex and one edge collection |

For the ontology plus examples (about 3,300 triples), PGT produces roughly 260 collections and
2,500 documents in about a second.

## 4. Querying a PGT import

Each PGT document carries `_uri` (the full IRI), `_label` (the local name), and its datatype
properties as attributes.

```aql
// EC2 instances and the VPC each one runs in
FOR instance IN EC2Instance
    FOR vpc IN 1..1 OUTBOUND instance belongsToVPC
        RETURN { instance: instance._label, arn: instance.arn, vpc: vpc._label }
```

```aql
// Everything inside the production VPC, up to two hops away over any relationship
FOR vpc IN VPC
    FILTER vpc._label == "ProductionVPC"
    FOR v, e IN 1..2 ANY vpc GRAPH "AWSOntology"
        RETURN DISTINCT { resource: v._label, via: PARSE_IDENTIFIER(e._id).collection }
```

```aql
// The class hierarchy: direct subclasses of AWS Resource categories
FOR cls IN Class
    FILTER cls._label == "AWSResource"
    FOR sub IN 1..1 INBOUND cls subClassOf
        SORT sub._label
        RETURN sub._label
```

```python
import os
from arango import ArangoClient

db = ArangoClient(hosts="http://localhost:8529").db(
    "aws_ontology", username="root", password=os.environ["ARANGO_PASSWORD"]
)
for row in db.aql.execute(
    "FOR i IN EC2Instance FOR v IN 1..1 OUTBOUND i belongsToVPC RETURN [i._label, v._label]"
):
    print(row)
```

## 5. Loading your own AWS inventory

The examples in `ontology/examples.ttl` are fictional. To analyse a real environment, export
your AWS resources as RDF individuals typed with the ontology's classes (for example from
AWS Config or a resource inventory), merge them with `ontology/aws.ttl`, validate them with the
SHACL shapes in `ontology/aws.shapes.ttl`, and import the merged graph with the same tool or
directly with ArangoRDF:

```python
from arango_rdf import ArangoRDF
from rdflib import Graph

graph = Graph()
graph.parse("ontology/aws.ttl")
graph.parse("my_inventory.ttl")
ArangoRDF(db).rdf_to_arangodb_by_pgt("MyAWSInventory", graph, overwrite_graph=True)
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No ArangoDB password provided` | `export ARANGO_PASSWORD=...` or pass `--password` |
| `Failed to connect to ArangoDB` | Check `--host`, that the server is up (`curl .../_api/version`), and the credentials |
| Collection names clash with an application's | Import into a dedicated `--database` |
| Re-import leaves stale documents | Re-run without `--no-overwrite`, or drop the graph/database first |
