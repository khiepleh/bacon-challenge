from graph.query_degrees import bfs

from graph.parse_movies import build_connected_graph, new_movies

from server import bacon_errors

import flask

from os import getpid

import datetime
import json
import threading


class AtomicId():
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
            return self.value


app = flask.Flask(__name__)


g_actors_file = './preprocessed/actors.jsonl'
g_graph = None
g_req_id = AtomicId()
g_pid = getpid()
g_log_file = None


def server_log(id: int, msg: str):
    global g_pid
    global g_log_file

    print('[{}][{:<5}:{:<5}][server][0x{:0=16x}] {}'
          .format(
              datetime.datetime.now(), g_pid, threading.get_ident(), id, msg), file=g_log_file)


def get_degree(root: str, target: str):
    """Get the degree of separation between root and target.
    """
    return bfs(g_graph, root, target)


@app.route('/api', methods=['GET'])
def home():
    doc_body = {
        'bacon-number': {
            'Description': 'Returns the bacon number of the given actor', 'Parameters': {
                'actor': 'Actor to find the bacon number for'
            }
        },
        'actor-number': {
            'Description': 'Returns the degrees of separation between any two actors', 'Parameters': {
                'root': 'Root actor to search from', 'target': 'Target actor to search for'
            }
        },
        'movie': {
            'Description': 'Add a new movie to the dataset', 'Parameters': {}, 'Data': {
                'movie1': ['actor1', 'actor2', 'actorN'], 'movie2': ['actor1', 'actor2', 'actorN'], 'movieN': ['actor1', 'actor2', 'actorN']
            }
        },
        'multiple-degrees': {
            'Description': 'Query the degrees for multiple actor pairs in one request', 'Parameters': {}, 'Data': [
                ['actor1', 'actor2'], ['actor3', 'actor4'], ['actor1', 'actor4']
            ]
        }
    }

    return doc_body, 200


@app.route('/api/bacon-number', methods=['GET'])
def api_bacon():
    """Accepts one parameter - actor - and returns the bacon number for said actor.
    """
    try:
        req_id = g_req_id.increment()
        server_log(req_id, 'Processing bacon-number GET request')

        try:
            target = flask.request.args['actor']
        except KeyError:
            body = bacon_errors.missing_params
            body['Details'] = 'Missing parameter "actor"'

            server_log(req_id, '400: ' + body['Details'])

            return body, 400

        server_log(req_id, 'Querying Bacon number for {}'.format(target))

        root = 'Kevin Bacon'
        degree = get_degree(root, target)

        server_log(req_id, 'Got Bacon number of {} for {}'.format(degree, target))

        body = {}
        body['Results'] = [(root, target, degree)]
        body['Description'] = '"{}" is not in the dataset'.format(
            target) if degree == -2 else 'Success'
        return body, 200

    except:
        server_log(req_id, 'Unknown error processing bacon-number')
        return bacon_errors.unknown_error, 500


@app.route('/api/actor-number', methods=['GET'])
def api_arbitrary():
    """Accepts a root and target parameter and returns the degree of separation between them.
    """
    try:
        req_id = g_req_id.increment()
        server_log(req_id, 'Processing actor-number GET request')

        try:
            root = flask.request.args['root']
        except KeyError:
            body = bacon_errors.missing_params
            body['Details'] = 'Missing parameter "root"'

            server_log(req_id, '400: ' + body['Details'])

            return body, 400

        try:
            target = flask.request.args['target']
        except KeyError:
            body = bacon_errors.missing_params
            body['Details'] = 'Missing parameter "target"'

            server_log(req_id, '400: ' + body['Details'])

            return body, 400

        server_log(req_id, 'Querying degree for ({}, {})'.format(root, target))

        degree = get_degree(root, target)

        server_log(req_id, 'Got degree ({}, {}, {})'.format(
            root, target, degree))

        body = {}
        body['Results'] = [(root, target, degree)]

        # These are not errors - querying for actors that don't exist is considered valid
        # input and "we couldn't find a degree for X" is a valid response. Neither the
        # client nor server did anything wrong so a 4xx or 5xx seems misleading. This
        # applies to the other APIs which query degrees, too.
        if degree == -1:
            body['Description'] = '"{}" is not in the dataset'.format(root)

        elif degree == -2:
            body['Description'] = '"{}" is not in the dataset'.format(target)

        elif degree == -3:
            body['Description'] = 'Neither "{}" nor "{}" is in the dataset'.format(
                root, target)

        else:
            body['Description'] = 'Success'

        return body, 200

    except:
        server_log(req_id, 'Unknown error processing actor-number')
        return bacon_errors.unknown_error, 500


@app.route('/api/multiple-degrees', methods=['GET'])
def api_arbitrary_multi():
    """Accepts a JSON list of pairs of actors and returns the degrees of separation for each pair.

    Any single malformed pair will return a failure status code and cease processing, but
    any pairs that were queried successfully will be included to provide context for
    which pairs failed.
    """
    try:
        req_id = g_req_id.increment()
        server_log(req_id, 'Processing multiple-degrees GET request')

        try:
            pairs = json.loads(flask.request.data)
        except json.JSONDecodeError as e:
            body = bacon_errors.invalid_json
            body['Details'] = 'Parsing failed at pos {}, lineno {}, colno {}'.format(
                e.pos, e.lineno, e.colno)

            server_log(req_id, '400: ' + body['Details'])

            return body, 400

        if not len(pairs):
            server_log(req_id, 'No pairs provided')

            body = {}
            body['Results'] = []
            body['Description'] = 'No pairs provided'
            return body, 200

        successes = []
        try:
            for root, target in pairs:
                successes.append((root, target, get_degree(root, target)))
                server_log(req_id, 'Found {}'.format(successes[-1]))

        except ValueError:
            body = bacon_errors.multi_failed
            body['Details'] = '{} pairs succeeded; processing stopped at first failure: {}'.format(
                len(successes), json.dumps(successes))

            server_log(req_id, '400: ' + body['Details'])

            return body, 400

        server_log(
            req_id, 'Found degrees for all pairs successfully: {}'.format(successes))

        body = {}
        body['Results'] = successes
        body['Description'] = 'Degrees for {} pairs found successfully'.format(
            len(successes))
        return body, 200

    except:
        server_log(req_id, 'Unknown error processing multiple-degrees')
        return bacon_errors.unknown_error, 500


@app.route('/api/movie', methods=['POST'])
def api_new_movie():
    """Accepts a JSON map of movies -> casts which will be persisted across requests and runs.

    The persistence is on the actors file post-processing - the original dataset is unmodified.
    """
    try:
        req_id = g_req_id.increment()
        server_log(req_id, 'Processing movie POST request')

        try:
            movies = json.loads(flask.request.data)
        except json.JSONDecodeError as e:
            body = bacon_errors.invalid_json
            body['Details'] = 'Parsing failed at pos {}, lineno {}, colno {}'.format(
                e.pos, e.lineno, e.colno)

            server_log(req_id, '400: ' + body['Details'])

            return body, 400

        server_log(req_id, 'Adding new movies: {}'.format(movies))

        global g_actors_file
        global g_graph
        new_movies(movies, g_graph, g_actors_file)

        server_log(req_id, 'Successfully added new movies')

        body = {}
        body['Results'] = []
        body['Description'] = 'All movies added successfully'
        return body, 201

    except:
        server_log(req_id, 'Unknown error processing movie')
        return bacon_errors.unknown_error, 500


if __name__ == '__main__':
    try:
        server_log(0, 'Building connected graph; may take ~5-10 seconds')
        g_graph = build_connected_graph(g_actors_file)

    except:
        server_log(0, 'Unable to build graph; exiting')
        raise RuntimeError('Unable to build graph')

    with open('server.{}.log'.format(g_pid), 'w') as g_log_file:
        app.run()
