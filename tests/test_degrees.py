from graph.parse_movies  import build_connected_graph, sort_graph, new_movies_sorted
from graph.query_degrees import bfs_pre_sorted

from os import makedirs

import csv
import time


class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start


graph = build_connected_graph('preprocessed/actors.jsonl')
sort_graph(graph)

try:
    makedirs('test_results')
except:
    pass

log_file = 'test_results/test_results_{}.csv'.format(time.time())
with open(log_file, 'w', newline='') as lf:
    w = csv.writer(lf)
    w.writerow(['Root', 'Target', 'Time'])


def timeit(root, target, cond):
    with Timer() as t:
        assert bfs_pre_sorted(graph, root, target) == cond

    with open(log_file, 'a', newline='') as lf:
        w = csv.writer(lf)
        w.writerow([root, target, cond, t.interval])


# Sanity
def test_same():
    timeit('Kevin Bacon', 'Kevin Bacon', 0)


def test_not_exist():
    timeit('Kevin Bacon', 'Big Foot', -2)
    timeit('Big Foot', 'Kevin Bacon', -1)


# The Fellowship
def test_fellowship():
    timeit('Kevin Bacon', 'Elijah Wood', 2)
    timeit('Kevin Bacon', 'Sean Astin', 1)
    timeit('Kevin Bacon', 'Billy Boyd', 2)
    timeit('Kevin Bacon', 'Dominic Monaghan', 2)
    timeit('Kevin Bacon', 'Ian McKellen', 2)
    timeit('Kevin Bacon', 'Viggo Mortensen', 2)
    timeit('Kevin Bacon', 'Orlando Bloom', 1)
    timeit('Kevin Bacon', 'John Rhys-Davies', 2)
    timeit('Kevin Bacon', 'Sean Bean', 2)


# Poor cases, i.e. high degrees
def test_slow():
    timeit('Kevin Bacon', 'Douglas Fairbanks', 3)
    timeit('Kevin Bacon', 'Johnny Weissmuller', 3)
    timeit('Kevin Bacon', 'Sota Fukushi', 4)
    timeit('Douglas Fairbanks', 'Sota Fukushi', 4)

    # An actor who is not connected to the graph... at all!
    new_movies_sorted({'foo':['actor1']}, graph)
    timeit('Kevin Bacon', 'actor1', None)
