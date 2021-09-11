#!./venv/bin/python3

from rdflib import Graph, RDFS, RDF, URIRef, Literal, term
import rdflib

file_graph = Graph()
file_graph.parse("./graph/uploads/dublin_core_elements.nt")


def check_uriRef(val_to_check):
    if isinstance(val_to_check, URIRef):
        qname = file_graph.compute_qname(val_to_check)
        if qname[-1] is not None and qname[-1] != "":
            return qname[-1]
    return val_to_check


def main():
    for subject, predicate, obj in file_graph.triples((None, None, None)):
        print(check_uriRef(subject))
        print("subject: {}".format(subject))

        print(check_uriRef(predicate))
        print("predicate: {}".format(predicate))

        print(check_uriRef(obj))
        print("object: {}\n".format(obj))


if __name__ == "__main__":
    main()
