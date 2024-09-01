import wiki_scrapper

if __name__ == '__main__':
    LANGS = ["en", "fr", "es"]

    # create a list of main subjects for different graph sizes.

    subjects = {100: ["Mathematics", "Mathématiques", "Matemáticas"],
                500: ["Physics", "Physique", "Física"],
                1000: ["Biology", "Biologie", "Biología"]}

    setup_params = {'langs': ['en'], 'starting_points': ['London'], 'max_pages_per_lang': 100,
                    'removal_chance': 0, 'inversion_chance': 0, 'print_info': True, 'content': True, 'max_links': 5}
    save = True
    filename = 'Excavated Graphs/Mathematics_100_samples_graph.gpickle'

    # using scrapper to build the graph
    graph = wiki_scrapper.build_graph(True, save, **setup_params)
    print("Graph built\n\n")
    for node in graph.nodes:
        print(f"Vertex: {node}, Language: '{graph.nodes[node]['lang']}', Content: {graph.nodes[node]['content']}")
