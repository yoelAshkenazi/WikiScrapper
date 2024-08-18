# Wikipedia Graph Scrapper

## Yoel Ashkenazi

This repository contains methods and tools that help the creation of multilingual graphs with wikipedia subjects, with page hyperlinks as red edges, and page translations as blue edges.

### requirements
1. networkx
2. pywikibot
3. matplotlib

### usage
  1. clone this repository to your IDE.
  2. in 'main.py' there are the following:
     i. a list of languages to use.
     ii. a dictionary of possible starting points (fit for the given list of languages)
     iii. a dictionary of setup attirbutes. I recommend keeping the attributes as is, and only playing with the valuse of 'removal chance', 'inversion chance' and 'max pages'.
  3. after getting the desired attributes, you can execute the code:
  '''G = wiki_scrapper.build_graph(draw=True, save=True, **setup_params)'''
  where 'draw' is a flag indicating whether or not to draw the graph, 'save' is a flag for saving the graph as a .gpickle format for future usage outside the code, and 'setup_params' is the attribute dictionary from before.
