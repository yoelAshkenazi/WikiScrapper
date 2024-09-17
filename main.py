import wiki_scrapper


def build_content_graph(_name, _lang, **kwargs):
    """
    This function builds a graph of the content of the wikipedia pages.
    :param _name: the name of the graph.
    :param _lang: the language of the pages.
    :param kwargs: the setup parameters.
    :return: the graph.
    """
    _setup_params = {}
    for key, value in kwargs.items():
        _setup_params[key] = value

    _setup_params['langs'] = [_lang]
    _setup_params['starting_points'] = [_name]
    _setup_params['content'] = True
    _save = True

    # using scrapper to build the graph
    _graph = wiki_scrapper.build_graph(True, _save, **_setup_params)
    print("Graph built\n\n")
    return _graph


def build_multilang_graph(_names, _langs, **kwargs):
    """
    This function builds a graph of the content of the wikipedia pages in multiple languages.
    :param _names: the name of the graph. (will take the first element)
    :param _langs: the languages of the pages.
    :param kwargs: the setup parameters.
    :return: the graph.
    """
    _setup_params = {}
    for key, value in kwargs.items():
        _setup_params[key] = value

    _setup_params['langs'] = _langs
    _setup_params['starting_points'] = [_names]

    _save = True

    # using scrapper to build the graph
    _graph = wiki_scrapper.build_graph(True, _save, **_setup_params)
    print("Graph built\n\n")
    return _graph


if __name__ == '__main__':
    LANGS = ["en", "fr", "es"]

    # create a list of main subjects for different graph sizes.

    subjects = {100: ["Mathematics", "Mathématiques", "Matemáticas"],
                500: ["Physics", "Physique", "Física"],
                1000: ["Biology", "Biologie", "Biología"]}

    content_subjects = ['London', 'turtle', 'car', 'apple', 'clock']

    setup_params = {'langs': ['en'], 'starting_points': subjects[100], 'max_pages_per_lang': 100,
                    'removal_chance': 0, 'inversion_chance': 0, 'print_info': True, 'content': False, 'max_links': 5}
    save = True
    filename = 'Excavated Graphs/Mathematics_100_samples_graph.gpickle'

    # using scrapper to build the graph.
    # graph = wiki_scrapper.build_graph(True, save, **setup_params)

    for subject in content_subjects:
        graph = build_content_graph(subject, 'en', **setup_params)
        for node in graph.nodes:
            print(f"{node}: {graph.nodes()[node]['content']}")
        print("Graph built\n\n")
