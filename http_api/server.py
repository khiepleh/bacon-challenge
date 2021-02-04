from graph.query_degrees import bfs

from graph.parse_movies import build_connected_graph, new_movies

from http_api import bacon_errors

import flask

import json


app = flask.Flask(__name__)


g_actors_file = './preprocessed/actors.jsonl'
g_cache       = {}
g_graph       = None


def get_degree(root: str, target: str):
    """Get the degree of separation between root and target. Checks and updates the cache.
    """
    global g_cache

    try:
        root_cache = g_cache[root]
    except KeyError:
        g_cache[root] = {}
        root_cache    = g_cache[root]

    try:
        return root_cache[target]
    except KeyError:
        global g_graph
        degree             = bfs(g_graph, root, target)
        root_cache[target] = degree

    try:
        target_cache = g_cache[target]
    except KeyError:
        g_cache[target] = {}
        target_cache    = g_cache[target]

    if degree is None:
        target_cache[root] = None
        return degree

    elif degree >= 0 or degree == -3:
        target_cache[root] = degree

    # -1 means the root doesn't exist, -2 means the target doesn't exist
    elif degree == -1:
        target_cache[root] = -2

    elif degree == -2:
        target_cache[root] = -1

    return degree


@app.route('/api', methods=['GET'])
def home():
    doc_body = {
        'bacon-number' : {
              'Description' : 'Returns the bacon number of the given actor'
            , 'Parameters'  : {
                'actor' : 'Actor to find the bacon number for'
            }
        },
        'actor-number' : {
              'Description' : 'Returns the degrees of separation between any two actors'
            , 'Parameters'  : {
                  'root'   : 'Root actor to search from'
                , 'target' : 'Target actor to search for'
            }
        },
        'movie' : {
              'Description' : 'Add a new movie to the dataset'
            , 'Parameters'  : {}
            , 'Data'        : {
                  'movie1' : ['actor1', 'actor2', 'actorN']
                , 'movie2' : ['actor1', 'actor2', 'actorN']
                , 'movieN' : ['actor1', 'actor2', 'actorN']
            }
        },
        'multiple-degrees' : {
              'Description' : 'Query the degrees for multiple actor pairs in one request'
            , 'Parameters'  : {}
            , 'Data'        : [
                  ['actor1', 'actor2']
                , ['actor3', 'actor4']
                , ['actor1', 'actor4']
            ]
        }
    }

    return doc_body, 200


@app.route('/api/bacon-number', methods=['GET'])
def api_bacon():
    """Accepts one parameter - actor - and returns the bacon number for said actor.
    """
    try:
        try:
            target = flask.request.args['actor']
        except KeyError:
            body            = bacon_errors.missing_params
            body['Details'] = 'Missing parameter "actor"'
            return body, 400

        root = 'Kevin Bacon'
        degree = get_degree(root, target)

        body                = {}
        body['Results']     = [(root, target, degree)]
        body['Description'] = '"{}" is not in the dataset'.format(target) if degree == -2 else 'Success'
        return body, 200

    except:
        return bacon_errors.unknown_error, 500


@app.route('/api/actor-number', methods=['GET'])
def api_arbitrary():
    """Accepts a root and target parameter and returns the degree of separation between them.
    """
    try:
        try:
            root = flask.request.args['root']
        except KeyError:
            body            = bacon_errors.missing_params
            body['Details'] = 'Missing parameter "root"'
            return body, 400

        try:
            target = flask.request.args['target']
        except KeyError:
            body            = bacon_errors.missing_params
            body['Details'] = 'Missing parameter "target"'
            return body, 400

        degree = get_degree(root, target)

        body            = {}
        body['Results'] = [(root, target, degree)]

        if degree == -1:
            body['Description'] = '"{}" is not in the dataset'.format(root)

        elif degree == -2:
            body['Description'] = '"{}" is not in the dataset'.format(target)

        elif degree == -3:
            body['Description'] = 'Neither "{}" nor "{}" is in the dataset'.format(root, target)

        else:
            body['Description'] = 'Success'

        return body, 200

    except:
        return bacon_errors.unknown_error, 500


@app.route('/api/multiple-degrees', methods=['GET'])
def api_arbitrary_multi():
    """Accepts a JSON list of pairs of actors and returns the degrees of separation for each pair.

    Any single malformed pair will return a failure status code and cease processing, but
    any pairs that were queried successfully will be included to provide context for
    which pairs failed.
    """
    try:
        try:
            pairs = json.loads(flask.request.data)
        except json.JSONDecodeError as e:
            body            = bacon_errors.invalid_json
            body['Details'] = 'Parsing failed at pos {}, lineno {}, colno {}'.format(e.pos, e.lineno, e.colno)
            return body, 400

        if not len(pairs):
            body                = {}
            body['Results']     = []
            body['Description'] = 'No pairs provided'
            return body, 200

        successes = []
        try:
            for root, target in pairs:
                successes.append((root, target, get_degree(root, target)))
        except ValueError:
            body            = bacon_errors.multi_failed
            body['Details'] = '{} pairs succeeded: {}'.format(len(successes), json.dumps(successes))
            return body, 400

        body                = {}
        body['Results']     = successes
        body['Description'] = 'Degrees for {} pairs found successfully'.format(len(successes))
        return body, 200

    except:
        return bacon_errors.unknown_error, 500


@app.route('/api/movie', methods=['POST'])
def api_new_movie():
    """Accepts a JSON map of movies -> casts which will be persisted across requests and runs.

    The persistence is on the actors file post-processing - the original datset is unmodified.
    """
    try:
        try:
            movies = json.loads(flask.request.data)
        except json.JSONDecodeError as e:
            body = bacon_errors.invalid_json
            body['Details'] = 'Parsing failed at pos {}, lineno {}, colno {}'.format(e.pos, e.lineno, e.colno)
            return body, 400

        global g_actors_file
        global g_graph
        new_movies(movies, g_graph, g_actors_file)

        global g_cache
        g_cache.clear()

        body                = {}
        body['Results']     = []
        body['Description'] = 'All movies added successfully'
        return body, 201

    except:
        return bacon_errors.unknown_error, 500


if __name__ == '__main__':
    try:
        print('[server] Building connected graph; may take ~5-10 seconds.')
        g_graph = build_connected_graph(g_actors_file)

    except:
        print('[server] Unable to build graph; exiting.')
        exit(-1)

    app.run()

    # The server is not very safe and should generally not be exposed to the public.
    #app.run(host='0.0.0.0')
