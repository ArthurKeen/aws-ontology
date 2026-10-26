#!/usr/bin/env python3
"""
Logical consistency of the ontology together with its example instances (PRD REQ-015).

The structural DL checks in test_dl_compliance.py cannot see entailment-level defects such
as a property whose rdfs:domain, combined with the disjoint-category partitioning, forces an
example individual into two disjoint classes. These tests close that gap:

- a fast, dependency-free closure check (domain/range through sub/equivalent/inverse
  properties, plus the subclass hierarchy) that flags disjointness clashes, always run;
- a lint that rejects multiple named rdfs:domain/rdfs:range values on one property — OWL
  reads them as an *intersection*, which is almost never what the author meant;
- a full OWL 2 DL consistency check with HermiT (via owlready2), which needs a Java
  runtime. It is skipped when Java is absent unless REQUIRE_REASONER=1 (set in CI), so the
  ontology header's `:verificationMethod "owl-dl-reasoning"` claim is enforced, not assumed.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.base_test import BaseOntologyTest

try:
    from rdflib import OWL, RDF, RDFS, URIRef

    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False


def java_available() -> bool:
    """True only if a working JVM answers — macOS ships a /usr/bin/java stub without one."""
    if shutil.which("java") is None:
        return False
    try:
        return subprocess.run(["java", "-version"], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def local_name(term) -> str:
    return str(term).rsplit("#", 1)[-1]


@unittest.skipUnless(RDFLIB_AVAILABLE, "rdflib not available")
class TestConsistency(BaseOntologyTest):
    """Entailment-level consistency of aws.ttl + examples.ttl."""

    maxDiff = None

    def _superclasses(self, cls, cache: dict) -> set:
        if cls not in cache:
            cache[cls] = set()
            for parent in self.graph.objects(cls, RDFS.subClassOf):
                if isinstance(parent, URIRef):
                    cache[cls] |= {parent} | self._superclasses(parent, cache)
        return cache[cls]

    def _property_closure(self, prop, links: dict) -> set:
        """The property plus every super/equivalent property it entails."""
        seen, stack = {prop}, [prop]
        while stack:
            for nxt in links.get(stack.pop(), ()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    def test_multiple_domains_or_ranges_are_not_declared(self):
        """Multiple named rdfs:domain/range values are an intersection — use a superclass."""
        offenders = []
        for predicate in (RDFS.domain, RDFS.range):
            for prop in set(self.graph.subjects(predicate, None)):
                values = [v for v in self.graph.objects(prop, predicate) if isinstance(v, URIRef)]
                if len(values) > 1:
                    offenders.append(
                        f"{local_name(prop)} {predicate.n3(self.graph.namespace_manager)} "
                        f"{sorted(local_name(v) for v in values)}"
                    )
        self.assertEqual(offenders, [], "Intersection domain/range declarations found")

    def test_examples_do_not_entail_disjointness_clashes(self):
        """No example individual may be entailed into two disjoint classes."""
        examples = self.load_examples_graph()

        links: dict = {}
        for a, b in self.graph.subject_objects(RDFS.subPropertyOf):
            links.setdefault(a, set()).add(b)
        for a, b in self.graph.subject_objects(OWL.equivalentProperty):
            links.setdefault(a, set()).add(b)
            links.setdefault(b, set()).add(a)
        inverses: dict = {}
        for a, b in self.graph.subject_objects(OWL.inverseOf):
            inverses.setdefault(a, set()).add(b)
            inverses.setdefault(b, set()).add(a)

        def named(values):
            return {v for v in values if isinstance(v, URIRef)}

        types: dict = {}
        for s, o in examples.subject_objects(RDF.type):
            types.setdefault(s, set()).add(o)
        for s, p, o in examples:
            if p == RDF.type:
                continue
            for q in self._property_closure(p, links):
                types.setdefault(s, set()).update(named(self.graph.objects(q, RDFS.domain)))
                if isinstance(o, URIRef):
                    types.setdefault(o, set()).update(named(self.graph.objects(q, RDFS.range)))
                    for inv in inverses.get(q, ()):
                        types[o].update(named(self.graph.objects(inv, RDFS.domain)))
                        types[s].update(named(self.graph.objects(inv, RDFS.range)))

        cache: dict = {}
        disjoint = list(self.graph.subject_objects(OWL.disjointWith))
        clashes = []
        for individual, asserted in types.items():
            entailed = set(asserted)
            for cls in asserted:
                entailed |= self._superclasses(cls, cache)
            for a, b in disjoint:
                if a in entailed and b in entailed:
                    clashes.append(f"{local_name(individual)}: {local_name(a)} ⊓ {local_name(b)}")
        self.assertEqual(sorted(clashes), [], "Example individuals entailed into disjoint classes")

    def test_hermit_consistency(self):
        """Full OWL 2 DL consistency of ontology + examples under HermiT."""
        if not java_available():
            if os.environ.get("REQUIRE_REASONER") == "1":
                self.fail("REQUIRE_REASONER=1 but no Java runtime is available for HermiT")
            self.skipTest("Java runtime not available for HermiT")
        try:
            from owlready2 import OwlReadyInconsistentOntologyError, World, sync_reasoner
        except ImportError:
            if os.environ.get("REQUIRE_REASONER") == "1":
                self.fail("REQUIRE_REASONER=1 but owlready2 is not installed")
            self.skipTest("owlready2 not installed")

        merged = self.load_combined_graph()
        # examples.ttl imports the ontology by IRI; both are already merged locally.
        merged.remove((None, OWL.imports, None))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "merged.owl"
            merged.serialize(destination=str(path), format="xml")
            world = World()
            world.get_ontology(path.as_uri()).load()
            try:
                sync_reasoner(world, infer_property_values=False, debug=0)
            except OwlReadyInconsistentOntologyError as exc:
                self.fail(f"HermiT: ontology + examples is inconsistent: {exc}")
            unsatisfiable = [local_name(c.iri) for c in world.inconsistent_classes()]
        self.assertEqual(unsatisfiable, [], "Unsatisfiable classes")


if __name__ == "__main__":
    unittest.main(verbosity=2)
