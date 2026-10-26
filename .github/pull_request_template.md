## Summary

<!-- What does this change and why? Link AWS documentation for modelling changes. -->

## Checklist

- [ ] Edited `ontology/aws.ttl` (not `aws.owl`) and ran `tools/sync_formats.py ttl-to-owl`
- [ ] New classes/properties have `rdfs:label`, `rdfs:comment`, and a single domain/range
- [ ] Examples use placeholder account `123456789012` and fictional names
- [ ] `uv run pytest` passes
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
