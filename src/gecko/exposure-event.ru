PREFIX IHCC: <http://example.com/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

INSERT { ?s rdfs:subClassOf IHCC:exposure_event }
WHERE  { ?s a owl:Class }
