#!./venv/bin/python3

from rdflib import Graph, Namespace

from rdflib.namespace import RDF, RDFS, FOAF, XSD, DC, DCTERMS, _DCMITYPE


file_graph = Graph()
file_graph.parse("./graph/uploads/ontology.ttl")


def list():
    for s, p, o in file_graph:
        print("subject: {}\npredicate: {}\nobject{}\n".format(s, p, o))


def main():

    list()


if __name__ == "__main__":
    main()
