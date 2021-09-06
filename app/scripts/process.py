#!./venv/bin/python3

from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, XSD
import pprint

g = Graph()
g.parse("./graph/uploads/dublin_core_elements.nt")

print(len(g))

for s, p, o in g:
    print("{}".format(s))
