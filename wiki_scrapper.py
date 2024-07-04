import networkx as nx
import pywikibot
from pywikibot import textlib
from collections import deque
from typing import Tuple, List
import random
import pickle as pkl
import os
import matplotlib.pyplot as plt


BAD_CHARS = ['.', '#', ',', ':']  # characters that should not appear in a page title.


def build_graph(draw: bool = True, save: bool = False, **kwargs):
    """
    Build a graph with two colors representing edges, and colors for each vertex type.
    The graph is built using BFS for each language (red edges), and then vertices that are translations of each other
    are connected with blue edges.

    Args:
        draw (bool): Whether to draw the graph.
        save (bool): Whether to save the graph.
        **kwargs: Keyword arguments for the graph construction.

    Returns:
        nx.Graph: The constructed graph. (consists of red and blue edges,
        and each vertex has two attributes (lang, color) and an identifier (str)).
    """

    # initialize the parameters.
    languages = kwargs.get('langs', ["en", "fr", "es"])
    starting_points = kwargs.get('starting_points', ["Mathematics", "Mathématiques", "Matemáticas"])
    max_pages_per_lang = kwargs.get('max_pages_per_lang', 100)  # maximum number of pages per language.
    edge_removal_chance = kwargs.get('removal_chance', 0.8)  # chance of removing an edge.
    edge_inversion_chance = kwargs.get('inversion_chance', 0.1)  # chance of inverting an edge.
    print_info = kwargs.get('print_info', False)  # print the process information.
    bigsep = "-" * 100  # large separator.
    smallsep = "-" * 50  # small separator.

    G = nx.Graph()  # create a graph object.
    red_edges = []  # list to store the red edges.
    blue_edges = []  # list to store the blue edges.
    vertices_in_langs = {lang: set() for lang in languages}  # initialize the vertices in each language.

    # define the vertex colors.
    color_dict = {lang: '#' + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)]) for lang in languages}

    """
    Step 1: Get the connection pages. Add each visited vertex to the graph with 
    a language and color attributes.
    """

    if print_info:
        print(bigsep)

    for starting_point, selected_lang in zip(starting_points, range(len(languages))):  # go over the starting points.
        # perform BFS to get the connection pages.
        site = pywikibot.Site(languages[selected_lang])  # get the site object.

        # get the connection pages.
        queue = deque([starting_point])  # initialize the queue.
        vertices_in_lang = set()  # initialize the vertices in the language.
        while queue and len(vertices_in_lang) < max_pages_per_lang:  # while the queue is not empty.
            subject = queue.popleft()  # get the page.

            if subject not in vertices_in_lang:  # if the page is not visited.
                vertices_in_lang.add(subject)

            page = pywikibot.Page(site, subject)  # get the page object.

            # Get all linked pages in the first section of the page
            link_titles = get_section_links(page, site)

            # add neighbors while the number of vertices is less than the maximum.
            while len(vertices_in_lang) < max_pages_per_lang and link_titles:
                link = link_titles.pop(0)
                if link not in vertices_in_lang:
                    vertices_in_lang.add(link)  # add the vertex.
                    queue.append(link)  # add the vertex to the queue.
                red_edges.append((subject, link))  # add the edge.

        queue.clear()  # clear the queue.

        # Add the vertices to the graph.
        for vertex in vertices_in_lang:
            # add the vertex to the graph.
            G.add_node(vertex, lang=languages[selected_lang], color=color_dict[languages[selected_lang]])

        vertices_in_langs[languages[selected_lang]] = vertices_in_lang  # save the vertices in the language.

        if print_info:
            print(f"Visited {len(vertices_in_lang)} pages in '{languages[selected_lang]}'.")
            print(smallsep)

    """
    Step 2: Add the translations to the graph.
    For each vertex in each language, get the translations to the other languages and add to the graph.
    Try to connect the translation to the other vertices in the same language.
    """
    # Add the translations to the graph.
    if print_info:
        print(bigsep)
        print("Adding translations. Current vertices:", len(G.nodes))

    translations = {lang_: [] for lang_ in languages}  # initialize the translation dictionary. under every language,
    # it keeps all the translations from other languages to that language.
    new_vertices = set()
    for vertex in G.nodes:  # go over the vertices.
        lang = G.nodes[vertex]['lang']  # get the language of the vertex.
        site = pywikibot.Site(f'wikipedia:{lang}')  # get the site object.
        page = pywikibot.Page(site, vertex)  # get the page object.

        # get the translations of the page.
        langlinks = page.iterlanglinks()  # get the inter wiki links.
        langlinks = {link.site.code: link.title for link in langlinks if link.site.code in languages}  # filter

        # add the translations to the graph.
        for lang_, translation in langlinks.items():
            new_vertices.add((translation, lang_, color_dict[lang_]))  # add the translation to the new nodes.
            blue_edges.append((vertex, translation))  # add the blue edge.
            translations[lang_].append(translation)  # save the translation to the dictionary.

    # Add the new nodes to the graph.
    for v in new_vertices:  # go over the new vertices.
        G.add_node(v[0], lang=v[1], color=v[2])  # add the vertex to the graph.

    if print_info:
        print("Translations added. Current vertices:", len(G.nodes))

    # find red edges between translations in the same language.
    for lang_, translations in translations.items():
        site = pywikibot.Site(f'wikipedia:{lang_}')  # get the site object.
        for translation in translations:  # go over the translations.
            page = pywikibot.Page(site, translation)  # get the page object.

            # get the links in the first section of the page.
            link_titles = get_section_links(page, site)  # get the links.

            for title in link_titles:  # go over the links.
                if title in vertices_in_langs[lang_]:  # if the link is in the vertices.
                    red_edges.append((translation, title))  # add the red edge.

    # make the blue edges into cliques.
    for i in range(len(blue_edges)):
        for j in range(i + 1, len(blue_edges)):
            a, b = blue_edges[i]
            c, d = blue_edges[j]
            if b == c:
                blue_edges.append((a, d))
                continue
            if a == d:
                blue_edges.append((c, b))
                continue
            if a == c:
                blue_edges.append((b, d))
                continue
            if b == d:
                blue_edges.append((a, c))
                continue

    # remove self-links.
    for a, b in blue_edges:
        if a == b:
            blue_edges.remove((a, b))

    # Add the edges to the graph.
    G.add_edges_from(red_edges, color='red')  # add the red edges.
    G.add_edges_from(blue_edges, color='blue')  # add the blue edges.

    if print_info:
        print("Done.")
        print(bigsep)

    """
    Step 3: Apply edge removal and inversion.
    """
    if print_info:
        print("Applying edge removal and inversion.")

    for edge in list(G.edges):
        if random.random() < edge_inversion_chance:
            _invert_edge(G, edge)  # invert the edge.
        if random.random() < edge_removal_chance:
            _remove_edge(G, edge)  # remove the edge.

    if print_info:
        print("Done.")
        print(f"Created a graph with {G.number_of_nodes()} vertices and {G.number_of_edges()} edges.")
        print(bigsep)
        # temporary: print the blue edges.
        print("Blue edges:")
        for edge in G.edges:
            if G[edge[0]][edge[1]]['color'] == 'blue':
                print(edge)

    """
    Step 4: Draw and save the graph.
    """

    if draw:
        # draw the graph.
        pos = nx.spring_layout(G)
        edge_colors = nx.get_edge_attributes(G, 'color').values()
        node_colors = [color_dict[G.nodes[node]['lang']] for node in G.nodes]
        sizes = [100 for _ in G.nodes]
        nx.draw(G, pos, edge_color=edge_colors, node_color=node_colors, with_labels=False, node_size=sizes)

        if save:  # save the graph.
            try:
                filename = f'Figures/{starting_points[0]}_{max_pages_per_lang}_samples_graph.png'
                plt.savefig(filename)
            except OSError:
                os.makedirs('Figures')
                filename = f'Figures/{starting_points[0]}_{max_pages_per_lang}_samples_graph.png'
                plt.savefig(filename)

        plt.show()

    if save:  # save the graph.
        filename = f'Excavated Graphs/{starting_points[0]}_{max_pages_per_lang}_samples_graph.pkl'
        try:
            with open(filename, 'wb') as file:
                pkl.dump(G, file)
        except OSError:
            os.makedirs('Excavated Graphs')
            with open(filename, 'wb') as file:
                pkl.dump(G, file)

    return G


def _invert_edge(G: nx.Graph, edge: Tuple[str, str]):
    """
    Invert an edge in the graph.

    Args:
        G (nx.Graph): A networkx graph object.
        edge (Tuple[str, str]): The edge to invert.
    """
    color = G[edge[0]][edge[1]]['color']  # get the color of the edge.
    if color == 'red':
        G[edge[0]][edge[1]]['color'] = 'blue'
    else:
        G[edge[0]][edge[1]]['color'] = 'red'


def _remove_edge(G: nx.Graph, edge: Tuple[str, str]):
    """
    Remove an edge from the graph.

    Args:
        G (nx.Graph): A networkx graph object.
        edge (Tuple[str, str]): The edge to remove.
    """
    G.remove_edge(edge[0], edge[1])


def get_section_links(page: pywikibot.Page, site: pywikibot.Site) -> List:
    """
    Get the links in the first section of a page.

    Args:
        page (pywikibot.Page): The page object.
        site (pywikibot.Site): The site object.

    Returns:
        List: The links and the linked pages.
    """
    # Get all linked pages in the first section of the page
    sect = textlib.extract_sections(page.text, site)  # extract the sections of the page.
    link_titles = [link.group('title') for link in
                   pywikibot.link_regex.finditer(sect.header)]  # extract the links.

    # filter the links.
    link_titles = [link for link in link_titles if not any(char in link for char in BAD_CHARS)]
    link_titles = [link for link in link_titles if link != page.title()]  # remove the self-links.
    return list(link_titles)
