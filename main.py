import excavator


if __name__ == '__main__':

    LANGS = ["en", "fr", "es"]

    # create a list of main subjects for different graph sizes.

    subjects = {100: ["Mathematics", "Mathématiques", "Matemáticas"],
                500: ["Physics", "Physique", "Física"],
                1000: ["Biology", "Biologie", "Biología"]}

    setup_params = {'langs': LANGS, 'starting_points': subjects[100], 'max_pages_per_lang': 100, 'save': True,
                    'edge_removal_chance': 00, 'edge_inv_chance': 0, 'print_info': True}
    print(excavator.create_sample_graph(**setup_params))
