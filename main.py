import excavator
import pickle
import networkx as nx
import scrapper
import matplotlib.pyplot as plt
import wiki_scrapper


if __name__ == '__main__':

    LANGS = ["en", "fr", "es"]

    # create a list of main subjects for different graph sizes.

    subjects = {100: ["Mathematics", "Mathématiques", "Matemáticas"],
                500: ["Physics", "Physique", "Física"],
                1000: ["Biology", "Biologie", "Biología"]}

    setup_params = {'langs': LANGS, 'starting_points': subjects[100], 'max_pages_per_lang': 100,
                    'removal_chance': 0, 'inversion_chance': 0, 'print_info': True}
    filename = 'Excavated Graphs/Mathematics_100_samples_graph.gpickle'

    # using scrapper to build the graph
    graph = wiki_scrapper.build_graph(**setup_params)
