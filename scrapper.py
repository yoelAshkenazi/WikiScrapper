import networkx as nx
import pywikibot
from pywikibot import textlib
from collections import deque
from typing import List, Set, Tuple, Dict
import random
import pickle as pkl
import os
import matplotlib.pyplot as plt

BAD_CHARS = ['.', '#', ',', ':']  # characters that should not appear in a page title.


def get_connections(starting_point: str, max_pages: int, lang: str) -> (Set[str], List[Tuple[str, str]]):
    """
    Fetch linked pages starting from a given page up to a specified limit.

    Args:
        starting_point (str): The title of the starting page.
        max_pages (int): Maximum number of pages to fetch.
        lang (str): Language code of the Wikipedia (e.g., 'en' for English).

    Returns:
        Set[str]: A set of connected subjects.
        List[Tuple[str, str]]: A list of tuples (a, b) where b is a link from 'a'.
    """
    site = pywikibot.Site(lang, 'wikipedia')
    starting_page = pywikibot.Page(site, starting_point)

    visited = set()  # To keep track of visited pages
    connections = []  # To store the connections
    queue = deque([starting_page])  # Queue for BFS

    while queue and len(visited) < max_pages:
        page = queue.popleft()

        visited.add(page.title())
        # Get all linked pages in the first section of the page
        sect = textlib.extract_sections(page.text, site)  # extract the sections of the page.
        link_titles = [link.group('title') for link in pywikibot.link_regex.finditer(sect.header)]  # extract the links.

        # Filter the links.
        link_titles = [link for link in link_titles if not any(bad_char in link for bad_char in BAD_CHARS)]

        # filter self-links.
        links = [link for link in link_titles if link != page.title()]
        links = [pywikibot.Page(site, link) for link in links]

        left_pages = max_pages - len(visited)
        if left_pages < len(links):  # Randomly select a subset of links
            links = random.sample(links, left_pages)

        for link in links:  # Add connections
            connections.append((page.title(), link.title()))
            queue.append(link)

    return visited, connections


def get_all_translations(subjects: Set[str], lang: str, languages: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Fetch translations of given subjects in specified languages.

    Args:
        subjects (Set[str]): A set of subjects known to have Wikipedia pages.
        languages (List[str]): A list of language codes.
        lang (str): The language code of the subjects.

    Returns:
        Dict[str, Dict[str, str]]: A dictionary where keys are subject titles and values are dictionaries with
                                    language codes as keys and translation titles as values.
    """
    translations = {subject: {} for subject in subjects}

    site = pywikibot.Site(lang, 'wikipedia')

    for subject in subjects:
        page = pywikibot.Page(site, subject)
        langlinks = page.iterlanglinks()  # Get inter wiki links

        for link in langlinks:
            if link.site.code in languages:
                translations[subject][link.site.code] = link.title

    return translations


def find_matches(translations: Dict[str, Dict[str, str]]) -> List[Tuple[str, str]]:
    """
    Find matches between subjects and their translations.

    Args:
        translations (Dict[str, Dict[str, str]]): A dictionary where keys are subject titles and values are
                                                   dictionaries with language codes as keys and translation
                                                   titles as values.

    Returns:
        List[Tuple[str, str]]: A list of tuples (a, b) where b is a translation of a and both are in
                               the set of subjects.
    """
    matches = []

    for subject, trans_dict in translations.items():
        for lang_code, trans_title in trans_dict.items():
            if trans_title in translations:
                matches.append((subject, trans_title))

    return matches


def build_graph(subjects: Dict[str, Set[str]], connections: List[Tuple[str, str]],
                matches: List[Tuple[str, str]]) -> nx.Graph:
    """
    Build a graph from the connections and matches.

    Args:
        connections (List[Tuple[str, str]]): A list of tuples (a, b) where b is a link from 'a'.
        matches (List[Tuple[str, str]]): A list of tuples (a, b) where b is a translation of 'a'.
        subjects (Dict[Set[str]]): A dictionary of subjects for different languages.

    Returns:
        nx.Graph: A networkx graph object representing the connections and matches.
    """
    G = nx.Graph()

    # create a list of random colors for the vertices. (as many as the number of languages)
    # each color is a string of 6 characters representing a color in hexadecimal.
    COLORS = ['#' + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)]) for _ in range(len(subjects.keys()))]

    color_dict = {lang: color for lang, color in zip(subjects.keys(), COLORS)}

    for lang in subjects.keys():
        for subject in subjects[lang]:
            G.add_node(subject, lang=lang, color=color_dict[lang])

    for a, b in connections:  # Add connections (red edges)
        G.add_edge(a, b, color='red')

    for a, b in matches:  # Add matches (blue edges)
        G.add_edge(a, b, color='blue')

    return G


def complete_build(**kwargs):
    """
    Fetches connections and translations for a given subject in multiple languages and builds a graph.

    Args:
        **kwargs: Additional keyword arguments for the function.

    Returns:
        nx.Graph: A networkx graph object representing the connections and matches.
    """
    subjects = {}
    connections = []

    # Get the parameters
    langs = kwargs.get('langs', ['en', 'fr', 'es'])
    starting_points = kwargs.get('starting_points', ['Mathematics', 'Mathématiques', 'Matemáticas'])
    max_pages_per_lang = kwargs.get('max_pages_per_lang', 100)
    save = kwargs.get('save', False)
    print_info = kwargs.get('print_info', False)

    total_translations = []

    for i, lang in enumerate(langs):
        connected_subjects, connected_links = get_connections(starting_points[i], max_pages_per_lang, lang)
        subjects[lang] = connected_subjects

        if print_info:
            print(f"Got connections (red edges) in {lang} starting at {starting_points[i]}:\n"
                  f"Vertices: {len(connected_subjects)}\n"
                  f"Connections: {len(connected_links)}\n")

        translations = get_all_translations(connected_subjects, lang, langs)  # Get translations
        total_translations.append(translations)

        if print_info:
            print(f"Got translations in {lang}:\n{len(translations)}\n")

        connections += connected_links  # Add connections to the list

        if print_info:
            print(f"Vertices in {lang}: {len(connected_subjects)}")
            print(f"Connections in {lang}: {len(connected_links)}")
            print("-" * 50)

    # Find matches between subjects and their translations
    matches = find_matches(total_translations[0])

    if print_info:
        print(f"Total matches found: {len(matches)}")

    G = build_graph(subjects, connections, matches)

    if save:  # Save the graph
        filename = f'Excavated Graphs/{starting_points[0]}_{max_pages_per_lang}_samples_graph.pkl'
        try:
            with open(filename, 'wb') as file:
                pkl.dump(G, file)
        except FileNotFoundError:
            os.makedirs('Excavated Graphs')
            with open(filename, 'wb') as file:
                pkl.dump(G, file)

    # temporary-draw the graph
    draw(G)
    plt.show()
    return G
# todo- add edge inversion and removal.


def draw(G: nx.Graph):
    """
    Draw the graph.

    Args:
        G (nx.Graph): A networkx graph object.
    """

    print(G.nodes(data=True))
    print(G.edges(data=True))

    edge_colors = [G[u][v]['color'] for u, v in G.edges]
    vertex_colors = [G.nodes[v]['color'] for v in G.nodes]

    nx.draw(G, with_labels=True, edge_color=edge_colors, node_color=vertex_colors)
    plt.show()
