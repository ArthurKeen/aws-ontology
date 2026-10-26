# w3id.org redirect rules

The ontology's IRIs live under `https://w3id.org/arango-solutions/`. w3id.org is a community
redirect service; its rules are maintained by pull request to
<https://github.com/perma-id/w3id.org>.

`arango-solutions/` here mirrors the directory submitted there. To register or update:

1. Fork `perma-id/w3id.org`, copy `w3id/arango-solutions/` into the fork's root, open a PR.
2. After it is merged, check content negotiation:
   ```bash
   curl -sI -H 'Accept: text/turtle' https://w3id.org/arango-solutions/aws-ontology
   curl -sI -H 'Accept: application/rdf+xml' https://w3id.org/arango-solutions/aws-ontology/0.6.0
   ```

Until the redirect is live, tools can resolve the IRIs locally: Protégé uses
`ontology/catalog-v001.xml`, and rdflib-based tools load the files directly.
