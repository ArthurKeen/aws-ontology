# Contributing to the AWS Ontology

Thanks for helping improve the ontology. Issues and pull requests are welcome.

## Setup

```bash
git clone https://github.com/arango-solutions/AWS_Ontology.git
cd AWS_Ontology
uv sync                 # Python 3.11+, installs runtime + dev dependencies
uv run pre-commit install
uv run pytest
```

The HermiT consistency test needs a Java runtime (it is skipped locally without one, and
required in CI). The ArangoDB import test runs when `ARANGO_TEST_HOST` is set — see
[docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md).

## Changing the ontology

1. Edit **`ontology/aws.ttl`** — it is the source of truth. Never hand-edit `aws.owl`.
2. Before adding a class or property, check the name is not already used
   (`grep -n "^:NewName a owl:" ontology/aws.ttl`). Reusing a property name across unrelated
   domains can make the ontology inconsistent.
3. Give every class and property an `rdfs:label` and `rdfs:comment`. Give specific properties
   a single `rdfs:domain` / `rdfs:range`; if several classes apply, use (or add) a common
   superclass — multiple domain values mean *intersection* in OWL.
4. Place new resource classes under an existing top-level category (`ComputeResource`,
   `NetworkingResource`, ...) unless none fits.
5. Only give `:arn` values to resource types that really have ARNs (check the AWS
   Service Authorization Reference).
6. Add at least one example to `ontology/examples.ttl`, using placeholder account
   `123456789012` and fictional names — never real account data.
7. Regenerate and verify:
   ```bash
   uv run python tools/sync_formats.py ttl-to-owl
   uv run python tools/sync_formats.py check
   uv run pytest
   ```
8. Add a `CHANGELOG.md` entry under `[Unreleased]`.

Removing or renaming a class or property is a breaking change: mark it `owl:deprecated true`
first and keep it for at least one minor release.

## Pull requests

- Keep each PR focused; describe the AWS behaviour you are modelling, with a link to the AWS
  documentation.
- CI (lint, tests, OWL/TTL sync, HermiT, ArangoDB import) must pass.
- By contributing you agree that your contributions are licensed under the MIT License.

## Code of conduct

Be respectful and constructive. Maintainers may moderate discussions that are not.
