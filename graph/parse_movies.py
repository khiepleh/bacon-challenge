from typing import Dict, List, Set

import argparse
import csv
import json
import os
import time


def parse(csv_path: str, out_path: str):
    """Parses csv_path (the movies dataset's credits.csv) into out_path, a jsonl file.

    This function is intended to parse the credits.csv file from the movies dataset, and
    has undefined behaviour otherwise.
    """
    print('[parse_movies] Parsing {} into {}'.format(csv_path, out_path))

    start = time.time()
    with open(csv_path, 'r', encoding='utf8') as csv_file:
        with open(out_path, 'w', encoding='utf8') as out_file:
            credits_reader = csv.reader(csv_file)
            i = 0

            for row in credits_reader:
                i += 1

                # Skip the column labels
                if i == 1:
                    continue

                # This particular dataset is already a Python dict in string form, which we'll take advantage of.
                # In general, eval is a dangerous idea on un-sanitized data.
                cast  = eval(row[0])
                names = []
                for actor in cast:
                    names.append(actor['name'])

                out_file.write(json.dumps(names) + '\n')

                if i % 100 == 0:
                    print('[parse_movies] {} rows parsed'.format(i))

    print('[parse_movies] Finished parsing {} rows into {} in {} seconds'.format(i, out_path, time.time() - start))


# Edge weights are always 1 (omitted in practice).
Graph = Dict[str, Set[str]]

def build_connected_graph(actors_path: str) -> Graph:
    """Given a jsonl file of lists of actors (i.e. movie casts), return a connected Graph of actors linked to all of their 1st degree connections.

    Graph = dict[str, set[str]]
    Graphs effectively map one actor to a set of actors - their first degree connections.
    """
    print('[parse_movies] Building connected graph from {}'.format(actors_path))

    start     = time.time()
    out_graph = {}
    for cast in open(actors_path, 'r', encoding='utf8'):
        cast_set = set(eval(cast))
        for actor in cast_set:
            try:
                out_graph[actor] |= cast_set
            except KeyError:
                out_graph[actor] = cast_set.copy()
            out_graph[actor].remove(actor)

    print('[parse_movies] Built connected graph in {} seconds'.format(time.time() - start))

    return out_graph


Movies = Dict[str, List[str]]

def new_movies(movies: Movies, graph: Graph, actors_file: str=None):
    """Add new movies to an existing Graph.

    Movies = dict[str, list[str]]
    Movies maps movie titles to lists of actors (i.e. casts). The titles are unused and irrelevant.
    """
    print('[parse_movies] Adding new movies to graph')

    for cast in movies.values():
        cast_set = set(cast)
        for actor in cast_set:
            try:
                graph[actor] |= cast_set
            except KeyError:
                graph[actor] = cast_set.copy()
            graph[actor].remove(actor)

    if actors_file:
        with open(actors_file, 'a', encoding='utf8') as af:
            for cast in movies.values():
                af.write(json.dumps(cast) + '\n')


def main():
    parser = argparse.ArgumentParser(description='Parse the Movies Dataset credits.csv into a form which is readily-consumable for the Bacon Challenge.')
    parser.add_argument('csv', help='The credits.csv file containing the original Movies Dataset actor information.')
    parser.add_argument('-p', '--parsed-output', default='preprocessed/actors.jsonl', help='Path to the desired output file for parsed data; by default, preprocessed/actors.jsonl.')

    args = parser.parse_args()
    out  = args.parsed_output
    if not os.path.exists(out):
        try:
            os.makedirs(os.path.dirname(out))
        except:
            print('[parse_movies] Could not create output directory; will try to open output file anyway')

    parse(args.csv, out)


if __name__ == '__main__':
    main()
