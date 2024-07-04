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


def get_connection_pages(starting_point, selected_lang, langs, max_pages: int = 100):
    """
    This function returns the pages that are connected to the starting point.
    :param starting_point: starting point.
    :param langs: list of languages.
    :param selected_lang: index of the selected language.
    :param max_pages: maximum number of pages per language.
    :return:
    """

    translations = []  # translations dictionary from the starting point's
    # language to the others.
    vertices = set()  # set of vertices in the same language as the starting point.
    connections = []  # list of connections.
    sites = [pywikibot.Site(f'wikipedia:{lang}') for lang in langs]  # get the site objects.
    # Add vertices and translations.
    vertices.add(starting_point)  # add the starting point to the set of vertices.
    site = sites[selected_lang]  # get the site object.
    starting_page = pywikibot.Page(site, starting_point)  # get the page object.
    links_Q = get_links(starting_page, site)  # get the links in the starting point.

    for link in links_Q:  # add the links to the set of vertices.
        if link in vertices:  # if the link is already visited.
            continue
        vertices.add(link)
        connections.append((starting_point, link))

    while links_Q and len(vertices) <= max_pages:
        current_link = links_Q.pop(0)
        current_page = pywikibot.Page(site, current_link)  # get the page object.
        links = get_links(current_page, site)  # get the links in the current page.

        # Add the links to the queue. (if they are not already visited)
        slice_idx = min(len(links), max_pages - len(vertices))  # get the slice index.
        if slice_idx == len(links):  # if the max pages is not reached.
            links_Q.extend([link for link in links if link not in vertices])  # add the links to the queue.
        else:
            links = links[:slice_idx]  # slice the links.
            links_Q = []  # empty the queue.
        vertices.update(set(links))  # add the links to the set of vertices.
        connections.extend([(current_link, link) for link in links])

        print(f"Vertices: {len(vertices)}, lang: {langs[selected_lang]}")

    # Add translations.
    for v in vertices:
        v_page = pywikibot.Page(site, v)  # get the page object.
        translation_titles = [link_.title for link_ in v_page.iterlanglinks() if link_.site in sites
                              and link_.site != site]
        translation_titles.append(v)  # add the original title.
        translations.append(translation_titles)  # add the translations.
    print(f"Translations: {len(translations)}: {translations}")
    return vertices, translations, connections


def get_translation_edges(vertices, translations):
    """
    This function returns the translation edges between the vertices.
    :param vertices: set of vertices.
    :param translations: dictionary of translations.
    :return: list of translation edges.
    """
    translation_edges = []  # list of translation edges.

    # Add the translation edges.
    for translation in translations:
        if len(translation) < 2:  # no translations.
            continue

        for i in range(len(translation) - 1):
            for j in range(i + 1, len(translation)):
                if translation[i] in vertices and translation[j] in vertices:
                    translation_edges.append((translation[i], translation[j]))  # add the translation edge.
    return translation_edges


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
    bigsep = "-" * 100  # large separator.
    smallsep = "-" * 50  # small separator.

    # initialize the vertices, translations, and new red edges.
    vertices, total_translations = {}, []  # initialize the vertices and translations.
    total_red_edges = []

    if print_info:
        print(bigsep)

    # get the connection pages.

    for starting_point, selected_lang in zip(starting_points, range(len(langs))):
        # get the connection pages.
        vertices[selected_lang], new_translations, new_red_edges = (
            get_connection_pages(starting_point, selected_lang, langs, max_pages_per_lang))

        # add the new translations.
        # don't add the translations that are already in the total translations.
        for translation in new_translations:
            if list(set(translation)) not in total_translations:
                total_translations.append(translation)

        # add the new red edges.
        total_red_edges.extend(new_red_edges)

        if print_info:
            print(f"Vertices in {langs[selected_lang]}: {len(vertices[selected_lang])}")
            print(vertices[selected_lang])
            print(smallsep)
    print(total_translations)
    # get the translation edges.
    all_vertices = set().union(*vertices.values())
    translation_edges = get_translation_edges(all_vertices, total_translations)

    print(vertices)
    print(total_translations)
    print("translation edges", translation_edges)
    print("red edges", total_red_edges)
    # create the graph.
    G = nx.Graph()  # create a graph object.

    for lang in langs:  # add the vertices to the graph.
        G.add_nodes_from(vertices[langs.index(lang)], type=lang)

    G.add_edges_from(translation_edges, color='blue')  # add the translation edges to the graph.
    G.add_edges_from(total_red_edges, color='red')  # add the red edges to the graph.

    if print_info:
        print(bigsep)
        print(f"Number of nodes: {G.number_of_nodes()}")
        print(f"Number of edges: {G.number_of_edges()}")
        print(bigsep)

    # invert and remove edges.
    for edge in list(G.edges):
        if random.random() < edge_inversion_chance:  # invert the edge.
            invert_edge(G, edge)
        if random.random() < edge_removal_chance:  # remove the edge.
            remove_edge(G, edge)

    if save:
        # save the graph.
        filename = f"Excavated Graphs/{starting_points[0]}_{max_pages_per_lang}_samples_graph.pkl"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            pkl.dump(G, f)

    return G
