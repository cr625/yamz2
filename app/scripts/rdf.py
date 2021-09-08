#!./venv/bin/python3

from rdflib import Graph, URIRef

url_graph = Graph()

url_graph.parse(
    "https://www.dublincore.org/specifications/dublin-core/dcmi-terms/dublin_core_elements.nt"
)

for (subj, pred, obj) in url_graph:
    # Check if there is at least one triple in the Graph
    if ((subj, pred, obj)) not in url_graph:
        raise Exception("It better be!")
    print((subj, pred, obj))
