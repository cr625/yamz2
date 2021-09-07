#!./venv/bin/python3
import sched
from webbrowser import get
from rdflib import Graph
from rdflib import URIRef, Literal, Namespace
import rdflib
from rdflib.namespace import (
    CSVW,
    DC,
    DCAT,
    DCTERMS,
    DOAP,
    FOAF,
    ODRL2,
    ORG,
    OWL,
    PROF,
    PROV,
    RDF,
    RDFS,
    SDO,
    SH,
    SKOS,
    SOSA,
    SSN,
    TIME,
    VOID,
    XMLNS,
    XSD,
)


import pprint

file_graph = Graph()
file_graph.parse("./graph/uploads/dublin_core_elements.nt")

# graph
def print_graph():
    for stmt in file_graph:
        pprint.pprint(stmt)


def get_property():
    fgv = file_graph.value(None, RDFS.isDefinedBy, DC.publisher)
    print(fgv)
    # only prints the first


def get_properties():
    for s, p, o in file_graph.triples((DC.publisher, RDFS.isDefinedBy, None)):
        print("{}\n{}\n{}".format(s, p, o))
    # only prints the first


entries = []


def isDefineBy():
    for o in file_graph.objects(None, RDFS.isDefinedBy):
        if o not in entries:
            entries.append(o)
        schema = o
    print(len(entries))
    print(schema)


def get_schema():
    x = file_graph.value(DC.publisher, RDFS.isDefinedBy)
    print(x)


def get_all():
    for s, p, o in file_graph:
        print("s: {}\np: {}\no: {}\n".format(s, p, o))


def serialize_graph():
    sg = file_graph.serialize()
    print(sg)


# graph.namespaces
def print_graph_namespaces():
    for prefix, ns in file_graph.namespaces():
        print(prefix, ns)


def ob():
    entries = []
    for o in file_graph.objects(None, RDFS.isDefinedBy):
        if o not in entries:
            entries.append(o)
        schema = o
    # find all subjects of any type
    for s, p, o in file_graph.triples((None, None, None)):
        i = s.rfind(schema)
        s = s[i + len(schema) :]
        print("subject: {}".format(s))

        p = p[i + len(schema) :]
        print("predicate: {}".format(p))

        o = o[i + len(schema) :]
        print("object: {}\n".format(o))


def main():

    ob()


# get_properties()
# serialize_graph()
# print_graph()
# print_graph_namespaces()
# print_dc_elements()


if __name__ == "__main__":
    main()
