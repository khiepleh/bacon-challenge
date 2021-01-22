from graph.query_degrees import bfs_pre_sorted

from graph.parse_movies import build_connected_graph, sort_graph, new_movies_sorted

import flask

import json


app = flask.Flask(__name__)


actors_file = './preprocessed/actors.jsonl'

try:
    print('[server] Building connected graph; may take ~5 seconds.')
    connected_graph = build_connected_graph(actors_file)

    print('[server] Sorting the graph; may take ~5-10 seconds.')
    sort_graph(connected_graph)

except:
    print('[server] Unable to build and sort graph; exiting.')
    exit()

global_cache = {}


def get_degree(root: str, target: str):
    # This function is hard to read compared to the complexity of its behaviour - could use some tidying.
    try:
        root_cache = global_cache[root]
    except KeyError:
        global_cache[root] = {}
        root_cache         = global_cache[root]

    try:
        return root_cache[target]
    except KeyError:
        degree             = bfs_pre_sorted(connected_graph, root, target)
        root_cache[target] = degree

    try:
        target_cache = global_cache[target]
    except KeyError:
        global_cache[target] = {}
        target_cache         = global_cache[target]

    target_cache[root] = degree

    return degree


@app.route('/', methods=['GET'])
def home():
    return 'This API fetches "bacon numbers" for arbitrary actors'

###################################################################################################
# API
#
# Error handling on all of the API endpoints is... basic. Ideally, these should return specific
# error codes/messages indicating what went wrong. They should be pretty stable, though (i.e.
# won't crash the server).
#
# Additionally, the user input isn't sanitized or validated *at all*, so this server is not safe
# to expose publicly. "eval()" is never run directly on user input, at least.
###################################################################################################


@app.route('/api/bacon-number', methods=['GET'])
def api_bacon():
    try:
        actor = flask.request.args['actor']
        degree = get_degree('Kevin Bacon', actor)
        if degree == -2:
            return '{} is not in the dataset!'.format(actor)

        return str(degree)

    except:
        return 'Failure'


@app.route('/api/actor-number', methods=['GET'])
def api_arbitrary():
    try:
        root   = flask.request.args['root']
        target = flask.request.args['target']
        degree = get_degree(root, target)
        if degree == -1:
            return '{} is not in the dataset!'.format(root)

        if degree == -2:
            return '{} is not in the dataset!'.format(target)

        if degree == -3:
            return 'Neither {} nor {} is in the dataset!'.format(root, target)

        return str(degree)

    except:
        return 'Failure'


@app.route('/api/movie', methods=['POST'])
def api_new_movie():
    try:
        movies = json.loads(flask.request.data)
        new_movies_sorted(movies, connected_graph, actors_file)

    except:
        return 'Failure'

    return 'Success'


app.run()

# The server is not very safe and should generally not be exposed to the public.
#app.run(host='0.0.0.0')
