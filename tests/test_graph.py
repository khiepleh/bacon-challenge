from graph.parse_movies import build_connected_graph, new_movies

import operator


def verify_graph(jl_file, g_file):
    g = build_connected_graph(jl_file)
    with open(g_file) as gf:
        r = eval(gf.read())
        for k, v in g.items():
            assert sorted(r[k]) == sorted(v)


basic_jl  = 'tests/test_graphs/basic.jsonl'
basic_gr  = 'tests/test_graphs/basic.graph'
linear_jl = 'tests/test_graphs/linear.jsonl'
linear_gr = 'tests/test_graphs/linear.graph'
break_jl = 'tests/test_graphs/break_two_way_search.jsonl'
break_gr = 'tests/test_graphs/break_two_way_search.graph'


# Graph construction
def test_basic_graph():
    verify_graph(basic_jl, basic_gr)


def test_linear():
    verify_graph(linear_jl, linear_gr)


def test_break_two_way():
    verify_graph(break_jl, break_gr)


def test_modify():
    g = build_connected_graph(basic_jl)

    new = {
          'foo' : ['D', 'E', 'F']
        , 'bar' : ['A', 'E']
        , 'mux' : ['B', 'F']
        , 'qaz' : ['A', 'B']
    }

    new_movies(new, g)

    r = {
          'A' : ['B', 'C', 'E']
        , 'B' : ['A', 'C', 'F']
        , 'C' : ['A', 'B']
        , 'D' : ['E', 'F']
        , 'E' : ['A', 'D', 'F']
        , 'F' : ['B', 'D', 'E']
    }

    for k, v in g.items():
        assert sorted(r[k]) == sorted(v)
