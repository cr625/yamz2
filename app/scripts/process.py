#!./venv/bin/python3

from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, XSD, term
from rdflib.namespace import SKOS, DC, DCTERMS
import pprint

g = Graph()
g.parse("./graph/uploads/dublin_core_elements.nt")


def check_char(x):
    i = -1
    if "#" in x:
        i = x.rfind("#")
    elif "/" in x and not x.endswith("/"):
        i = x.rfind("/")
    return x[i + 1 :].strip()


for s, p, o in g:
    s = check_char(s)
    print("subject: {}".format(s))

    p = check_char(p)
    print("predicate: {}".format(p))

    o = check_char(o)
    print("object: {}\n".format(o))
