import networkx as nx
import pywikibot
from pywikibot import textlib
import random
import pickle as pkl
import os

BAD_CHARS = ['.', '#', ',', ':']  # characters that should not appear in a page title.


def get_links(page, site):
    """
    This function returns a list of links in the page.
    :param page: page object.
    :param site: site object.
    :return: list of links in the page.
    """
    sect = textlib.extract_sections(page.text, site)  # extract the sections of the page.
    links = [link.group('title') for link in pywikibot.link_regex.finditer(sect.header)]  # extract the links.

    # Filter the links.
    links = [link for link in links if not any(bad_char in link for bad_char in BAD_CHARS)]

    # filter self-links.
    links = [link for link in links if link != page.title()]

    return links


def invert_edge(G, edge):
    """
    This function inverts the edge in the graph.
    :param G: graph object.
    :param edge: edge to invert.
    :return: None.
    """
    u, v = edge
    color = G[u][v]['color']  # get the color of the edge.
    if color == 'red':
        G[u][v]['color'] = 'blue'
    else:
        G[u][v]['color'] = 'red'


def remove_edge(G, edge):
    """
    This function removes the edge from the graph.
    :param G: graph object.
    :param edge: edge to remove.
    :return: None.
    """
    G.remove_edge(*edge)


def create_sample_graph(**setup_params):
    """
    This method creates a page graph for each language, and then combines them into a single graph.
    Two vertices from the same language are connected if they are linked to one another.
    Two vertices from different languages are connected if they are translations of one another.
    of the same subject in a different language.
    :param setup_params: parameters for the graph.
    :return:
    """

    # initialize the starting point and languages.
    langs = setup_params.get('langs', ["en", "fr", "es"])
    starting_points = setup_params.get('starting_points', ["Mathematics", "Mathématiques", "Matemáticas"])

    # initialize the graph parameters.
    max_pages_per_lang = setup_params.get('max_pages_per_lang', 100)  # maximum number of pages per language.
    save = setup_params.get('save', False)  # save the graph.
    edge_removal_chance = setup_params.get('edge_removal_chance', 0.8)  # chance of removing an edge.
    edge_inversion_chance = setup_params.get('edge_inv_chance', 0.1)  # chance of inverting an edge.

    print_info = setup_params.get('print_info', False)  # print the process information.
    if print_info:
        bigsep = "-" * 100  # large separator.
        smallsep = "-" * 50  # small separator.

    # initialize the vertices and edges.
    vertices = {lang: set() for lang in langs}
    edges = {lang: list() for lang in langs}

    if print_info:
        print(bigsep)  # Large separator.
        print(f"Excavating {max_pages_per_lang} pages for '{langs}' starting from {starting_points}...")
        print(smallsep)  # Small separator.

    for lang, starting_point in zip(langs, starting_points):  # iterate over the languages and starting points.

        # Add the starting point to the set of vertices for the current language.
        vertices[lang].add(starting_point)
        site = pywikibot.Site(f'wikipedia:{lang}')

        # Add the starting neighbors to the set of vertices for the current language.
        page = pywikibot.Page(site, starting_point)

        # Get the links in the starting page.
        links = get_links(page, site)

        # Add the links to the set of vertices for the current language.
        vertices[lang].update(set(links))

        # Add the edges between the starting point and its neighbors.
        edges[lang].extend([(starting_point, link) for link in links])

        # Make a queue of the links to visit.
        Q = links.copy()

        if print_info:
            print(f"Successfully excavated {starting_point}. ({len(vertices[lang])} neighbors in total.)")
            print(smallsep)
        # Visit the neighbors of the new vertices.
        while len(vertices[lang]) < max_pages_per_lang and Q:
            current_link = Q.pop(0)  # get the first link in the queue.

            # define the current page.
            page = pywikibot.Page(site, current_link)

            # Get the links in the current page.
            links = get_links(page, site)

            # Add the links to the queue. (if they are not already visited)
            Q.extend([link for link in links if link not in vertices[lang]])

            # add the links to the set of vertices for the current language.
            vertices[lang].update(set(links))

            # Add the edges between the current link and its neighbors.
            edges[lang].extend([(current_link, link) for link in links])

    if print_info:
        print(f"Completed the excavation process. The graph has {sum([len(verts) for verts in vertices.values()])}"
              f" vertices.")
        print("-" * 20)
        print("Combining the graphs...")

    # Create the graph.
    G = nx.Graph()

    # Add the vertices to the graph.
    for lang in langs:
        for vertex in vertices[lang]:
            G.add_node(vertex, type=lang)

    # Add the red edges to the graph. (similarity measure)
    for lang in langs:
        edges[lang] = set(edges[lang])  # remove duplicates.
    red_edges = [edge for lang in langs for edge in edges[lang]]  # combine the edges.

    # Add the red edges to the graph.
    for edge in red_edges:
        G.add_edge(edge[0], edge[1], color='red')

    # Add the blue edges to the graph. (translation measure)
    for lang1 in langs:
        for lang2 in langs:
            if lang1 == lang2:  # skip the same language.
                continue

            # iterate over the vertices in lang1.
            for vertex1 in vertices[lang1]:

                # iterate over the vertices in lang2.
                for vertex2 in vertices[lang2]:

                    # create the site objects.
                    site1 = pywikibot.Site(f'wikipedia:{lang1}')
                    site2 = pywikibot.Site(f'wikipedia:{lang2}')

                    # create the page objects.
                    page1 = pywikibot.Page(site1, vertex1)
                    page2 = pywikibot.Page(site2, vertex2)

                    # check if the pages are translations of one another.
                    if not (page1.exists() and page2.exists()):  # check if the pages exist.
                        continue

                    # get interlanguage links.
                    lang_links = page1.langlinks()

                    # check if the pages are translations of one another.
                    for link in lang_links:
                        if link.site.code == lang2 and link.title == vertex2:
                            G.add_edge(vertex1, vertex2, color='blue')
                            break
    if print_info:
        print("Successfully combined the graphs.")
        print(smallsep)
        print("Applying the edge removal and inversion...")

    # apply the edge removal and inversion.
    removal_flag = edge_removal_chance > 0
    inversion_flag = edge_inversion_chance > 0

    if inversion_flag:  # check inversion first.
        for edge in G.edges():
            if random.random() < edge_inversion_chance:
                invert_edge(G, edge)
    if removal_flag:  # check removal second.
        for edge in G.edges():
            if random.random() < edge_removal_chance:
                remove_edge(G, edge)

    if print_info:
        print("Successfully applied the edge removal and inversion.")
        print(smallsep)
        print("Saving the graph...")
    # save the graph.
    if save:
        filename = (f"{starting_points[0]}_{max_pages_per_lang * len(langs)}_samples_{edge_inversion_chance}_"
                    f"inversions_{edge_removal_chance}_removals_graph.pkl")
        dirname = "Excavated Graphs"
        try:
            with open(f"{dirname}/{filename}", 'wb') as f:
                pkl.dump(G, f)
        except OSError:  # if the directory does not exist.
            os.mkdir(dirname)  # create the directory.
            with open(f"{dirname}/{filename}", 'wb') as f:
                pkl.dump(G, f)

        if print_info:
            print(f"Successfully saved the graph at {filename}.")
            print(bigsep)

    return G
