# SPARQL Query Examples for AWS Ontology

## 🎯 Overview

These SPARQL queries demonstrate the power of your enhanced AWS Ontology. Use them in Protégé's SPARQL Query tab or any SPARQL endpoint.

## 📋 Basic Queries

### 1. List All Classes
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?class ?label WHERE {
  ?class a owl:Class .
  OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?label
```

### 2. Find All Container Services
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?service ?label WHERE {
  ?service rdfs:subClassOf* :ComputeResource .
  ?service rdfs:label ?label .
  FILTER(
    CONTAINS(?label, "ECS") || 
    CONTAINS(?label, "EKS") || 
    CONTAINS(?label, "Fargate") ||
    CONTAINS(?label, "Container")
  )
}
```

### 3. API & Integration Services
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?service ?label WHERE {
  {
    ?service rdfs:subClassOf* :NetworkingResource .
    ?service rdfs:label ?label .
    FILTER(CONTAINS(?label, "API"))
  }
  UNION
  {
    ?service rdfs:subClassOf* :IntegrationResource .
    ?service rdfs:label ?label .
  }
}
```

## 🔗 Relationship Queries

### 4. Services That Can Trigger Step Functions
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?service ?stepFunction WHERE {
  ?service :triggersStepFunction ?stepFunction .
  OPTIONAL { ?service rdfs:label ?serviceLabel }
  OPTIONAL { ?stepFunction rdfs:label ?stepFunctionLabel }
}
```

### 5. Container Orchestration Relationships
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?service ?cluster ?taskDef WHERE {
  ?service :runsOnCluster ?cluster .
  ?service :hasTaskDefinition ?taskDef .
  OPTIONAL { ?service rdfs:label ?serviceLabel }
  OPTIONAL { ?cluster rdfs:label ?clusterLabel }
}
```

### 6. Event-Driven Architecture Components
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?publisher ?topic ?subscriber WHERE {
  ?publisher :publishesToTopic ?topic .
  ?subscriber :subscribesTo ?topic .
  OPTIONAL { ?publisher rdfs:label ?pubLabel }
  OPTIONAL { ?topic rdfs:label ?topicLabel }
  OPTIONAL { ?subscriber rdfs:label ?subLabel }
}
```

## ⏰ Temporal Queries

### 7. Resource Creation Timeline
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?older ?newer WHERE {
  ?older :createdBefore ?newer .
  OPTIONAL { ?older rdfs:label ?olderLabel }
  OPTIONAL { ?newer rdfs:label ?newerLabel }
}
```

### 8. Migration Relationships
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?source ?target WHERE {
  ?target :migratedFrom ?source .
  OPTIONAL { ?source rdfs:label ?sourceLabel }
  OPTIONAL { ?target rdfs:label ?targetLabel }
}
```

### 9. Resource Replacement History
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?oldResource ?newResource WHERE {
  ?oldResource :replacedBy ?newResource .
  OPTIONAL { ?oldResource rdfs:label ?oldLabel }
  OPTIONAL { ?newResource rdfs:label ?newLabel }
}
```

## 💰 Cost & Financial Queries

### 10. Cost Allocation Relationships
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?charger ?charged WHERE {
  ?charger :incursChargeFor ?charged .
  OPTIONAL { ?charger rdfs:label ?chargerLabel }
  OPTIONAL { ?charged rdfs:label ?chargedLabel }
}
```

### 11. Resource Optimization Chains
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?optimizer ?optimized WHERE {
  ?optimizer :optimizes ?optimized .
  OPTIONAL { ?optimizer rdfs:label ?optimizerLabel }
  OPTIONAL { ?optimized rdfs:label ?optimizedLabel }
}
```

### 12. Shared Resource Networks
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?resource1 ?resource2 WHERE {
  ?resource1 :sharesResourcesWith ?resource2 .
  OPTIONAL { ?resource1 rdfs:label ?label1 }
  OPTIONAL { ?resource2 rdfs:label ?label2 }
}
```

## 🛡️ Compliance & Governance Queries

### 13. Compliance Status Overview
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?resource ?standard ?status WHERE {
  ?resource :complianceStandard ?standard .
  ?resource :complianceStatus ?status .
  OPTIONAL { ?resource rdfs:label ?resourceLabel }
}
```

### 14. Audit Relationships
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?auditor ?audited WHERE {
  ?auditor :audits ?audited .
  OPTIONAL { ?auditor rdfs:label ?auditorLabel }
  OPTIONAL { ?audited rdfs:label ?auditedLabel }
}
```

### 15. Control & Governance Hierarchy
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?controller ?controlled WHERE {
  ?controller :controls ?controlled .
  OPTIONAL { ?controller rdfs:label ?controllerLabel }
  OPTIONAL { ?controlled rdfs:label ?controlledLabel }
}
```

## 📊 Property Analysis Queries

### 16. All Object Properties with Domains and Ranges
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?property ?label ?domain ?range WHERE {
  ?property a owl:ObjectProperty .
  OPTIONAL { ?property rdfs:label ?label }
  OPTIONAL { ?property rdfs:domain ?domain }
  OPTIONAL { ?property rdfs:range ?range }
}
ORDER BY ?label
```

### 17. Functional Properties
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?property ?label WHERE {
  ?property a owl:FunctionalProperty .
  OPTIONAL { ?property rdfs:label ?label }
}
```

### 18. Transitive Properties
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?property ?label WHERE {
  ?property a owl:TransitiveProperty .
  OPTIONAL { ?property rdfs:label ?label }
}
```

## 🔧 Cardinality & Constraint Queries

### 19. Classes with Cardinality Restrictions
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?class ?property ?cardinality WHERE {
  ?class rdfs:subClassOf ?restriction .
  ?restriction a owl:Restriction .
  ?restriction owl:onProperty ?property .
  {
    ?restriction owl:cardinality ?cardinality
  } UNION {
    ?restriction owl:minCardinality ?cardinality
  } UNION {
    ?restriction owl:maxCardinality ?cardinality
  }
}
```

### 20. Disjoint Class Groups
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?class1 ?class2 WHERE {
  ?disjoint a owl:AllDisjointClasses .
  ?disjoint owl:members ?list .
  ?list rdf:rest*/rdf:first ?class1 .
  ?list rdf:rest*/rdf:first ?class2 .
  FILTER(?class1 != ?class2)
}
```

## 🧪 Testing & Validation Queries

### 21. Count Resources by Type
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?resourceType (COUNT(?resource) AS ?count) WHERE {
  ?resource rdfs:subClassOf* ?resourceType .
  ?resourceType rdfs:subClassOf :AWSResource .
  FILTER(?resourceType != :AWSResource)
}
GROUP BY ?resourceType
ORDER BY DESC(?count)
```

### 22. Verify Ontology Completeness
```sparql
PREFIX : <https://w3id.org/arango-solutions/aws-ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT 
  (COUNT(?class) AS ?totalClasses)
  (COUNT(?objectProp) AS ?objectProperties) 
  (COUNT(?dataProp) AS ?dataProperties)
WHERE {
  { ?class a owl:Class } UNION
  { ?objectProp a owl:ObjectProperty } UNION  
  { ?dataProp a owl:DatatypeProperty }
}
```

## 💡 Usage Tips

1. **Copy and paste** these queries into Protégé's SPARQL Query tab
2. **Modify prefixes** if your ontology uses different namespace URIs
3. **Add LIMIT clauses** for large result sets: `LIMIT 10`
4. **Use OPTIONAL** for properties that might not exist on all resources
5. **Filter results** with `FILTER()` functions for specific criteria
6. **Order results** with `ORDER BY` for better readability

## 🔗 Resources

- [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/)
- [Protégé SPARQL Query Plugin](https://protegewiki.stanford.edu/wiki/SPARQL_Query_Plugin)
- [W3C SPARQL Examples](https://www.w3.org/2009/Talks/0615-qbe/)