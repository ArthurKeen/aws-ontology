# Security Policy

The AWS Ontology is a data model plus helper scripts; it holds no credentials and runs no
service. Security-relevant issues are most likely in the tooling (for example the ArangoDB
importer or the monitoring automation), or real account data accidentally committed to the
examples.

## Reporting a vulnerability

Please **do not** open a public issue. Use GitHub's private vulnerability reporting:
**Security → Report a vulnerability** on
<https://github.com/arango-solutions-org/AWS_Ontology/security>.

We aim to acknowledge reports within five working days. If you find real AWS account
identifiers, ARNs, or credentials anywhere in this repository, report them the same way.
