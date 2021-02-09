from server import server

from graph.parse_movies import build_connected_graph

import pytest

import json
import os.path
import shutil


# make a fresh copy of the actors file so the 'new movies' tests don't mess up the original
tmp_actors = os.path.join(os.path.dirname(
    os.path.abspath(server.g_actors_file)), 'tmp_actors.jsonl')
shutil.copyfile(server.g_actors_file, tmp_actors)
server.g_actors_file = tmp_actors
server.g_graph = build_connected_graph(tmp_actors)


@pytest.fixture
def client():
    server.app.config['TESTING'] = True

    with server.app.test_client() as client:
        yield client


def test_api_doc(client):
    r = client.get('/api')
    j = r.get_json()

    assert r.status_code == 200
    assert j['bacon-number']
    assert j['actor-number']
    assert j['movie']
    assert j['multiple-degrees']


api_root = '/api'
api_bacon = api_root + '/bacon-number'
api_arbitrary = api_root + '/actor-number'
api_new = api_root + '/movie'
api_multi = api_root + '/multiple-degrees'


def test_bacon_simple(client):
    r = client.get(api_bacon, query_string={
                   'actor': 'Kevin Spacey', 'other': 'params', 'do not': 'matter'})
    j = r.get_json()

    assert r.status_code == 200
    assert j['Results'] == [['Kevin Bacon', 'Kevin Spacey', 2]]
    assert j['Description'] == 'Success'


def test_bacon_bacon(client):
    r = client.get(api_bacon, query_string={'actor': 'Kevin Bacon'})
    j = r.get_json()

    assert r.status_code == 200
    assert j['Results'] == [['Kevin Bacon', 'Kevin Bacon', 0]]
    assert j['Description'] == 'Success'


def test_bacon_not_in_data(client):
    r = client.get(api_bacon, query_string={'actor': 'Karsa Orlong'})
    j = r.get_json()

    assert r.status_code == 200
    assert j['Results'] == [['Kevin Bacon', 'Karsa Orlong', -2]]
    assert j['Description'] == '"Karsa Orlong" is not in the dataset'


def test_bacon_missing_param(client):
    r = client.get(api_bacon, query_string={
                   'but we': 'need', 'the param': 'actor'})
    j = r.get_json()

    assert r.status_code == 400
    assert j['Code'] == -2
    assert j['Details'] == 'Missing parameter "actor"'


def test_arbitrary_simple(client):
    r = client.get(api_arbitrary, query_string={
                   'target': 'Kevin Costner', 'root': 'Kevin Spacey', 'other': 'params', 'do not': 'matter'})
    j = r.get_json()

    assert r.status_code == 200
    assert j['Results'] == [['Kevin Spacey', 'Kevin Costner', 2]]
    assert j['Description'] == 'Success'


def test_arbitrary_same(client):
    r = client.get(api_arbitrary, query_string={
                   'target': 'Kevin Costner', 'root': 'Kevin Costner'})
    j = r.get_json()

    assert r.status_code == 200
    assert j['Results'] == [['Kevin Costner', 'Kevin Costner', 0]]
    assert j['Description'] == 'Success'


def test_arbitrary_root_not_in_data(client):
    r = client.get(api_arbitrary, query_string={
                   'target': 'Kevin Costner', 'root': 'Anomander Rake'})
    j = r.get_json()

    assert r.status_code == 200
    assert j['Results'] == [['Anomander Rake', 'Kevin Costner', -1]]
    assert j['Description'] == '"Anomander Rake" is not in the dataset'


def test_arbitrary_target_not_in_data(client):
    r = client.get(api_arbitrary, query_string={
                   'root': 'Kevin Costner', 'target': 'Dassem Ultor'})
    j = r.get_json()

    assert r.status_code == 200
    assert j['Results'] == [['Kevin Costner', 'Dassem Ultor', -2]]
    assert j['Description'] == '"Dassem Ultor" is not in the dataset'


def test_arbitrary_neither_in_data(client):
    r = client.get(api_arbitrary, query_string={
                   'root': 'Brys Beddict', 'target': 'Trull Sengar'})
    j = r.get_json()

    assert r.status_code == 200
    assert j['Results'] == [['Brys Beddict', 'Trull Sengar', -3]]
    assert j['Description'] == 'Neither "Brys Beddict" nor "Trull Sengar" is in the dataset'


def test_arbitrary_missing_target(client):
    r = client.get(api_arbitrary, query_string={
                   'root': 'Kevin Spacey', 'other': 'params', 'do not': 'matter'})
    j = r.get_json()

    assert r.status_code == 400
    assert j['Code'] == -2
    assert j['Details'] == 'Missing parameter "target"'


def test_arbitrary_missing_root(client):
    r = client.get(api_arbitrary, query_string={
                   'target': 'Kevin Spacey', 'other': 'params', 'do not': 'matter'})
    j = r.get_json()

    assert r.status_code == 400
    assert j['Code'] == -2
    assert j['Details'] == 'Missing parameter "root"'


def test_multi_simple(client):
    r = client.get(api_multi, json=[['Kevin Bacon', 'Kevin Spacey'], [
                   'Kevin Spacey', 'Kevin Costner'], ['Kevin Costner', 'Kevin Smith']])
    j = r.get_json()

    assert r.status_code == 200
    assert j['Results'] == [['Kevin Bacon', 'Kevin Spacey', 2], [
        'Kevin Spacey', 'Kevin Costner', 2], ['Kevin Costner', 'Kevin Smith', 2]]
    assert j['Description'] == 'Degrees for 3 pairs found successfully'


def test_multi_none(client):
    r = client.get(api_multi, json=[])
    j = r.get_json()

    assert r.status_code == 200
    assert j['Results'] == []
    assert j['Description'] == 'No pairs provided'


def test_multi_malformed(client):
    in_data = [['Kevin Bacon', 'Kevin Spacey', 'Kevin Costner']]
    r = client.get(api_multi, json=in_data)
    j = r.get_json()

    assert r.status_code == 400
    assert j['Code'] == -4
    assert j['Details'] == '0 pairs succeeded; processing stopped at first failure: []'


def test_multi_malformed_some_okay(client):
    in_data = [['foo', 'bar'], ['mux', 'qaz'], ['Kevin Bacon',
                                                'Kevin Spacey', 'Kevin Costner'], ['big', 'foot']]
    r = client.get(api_multi, json=in_data)
    j = r.get_json()

    assert r.status_code == 400
    assert j['Code'] == -4
    assert j['Details'] == '2 pairs succeeded; processing stopped at first failure: {}'.format(
        json.dumps([['foo', 'bar', -3], ['mux', 'qaz', -3]]))


def test_multi_invalid_json_simple(client):
    r = client.get(api_multi, data='foobar')
    j = r.get_json()

    assert r.status_code == 400
    assert j['Code'] == -3
    assert j['Details'] == 'Parsing failed at pos 0, lineno 1, colno 1'


def test_multi_invalid_json_complex(client):
    r = client.get(api_multi, data='{ "foobar" : "muxqaz", "actor" : None }')
    j = r.get_json()

    assert r.status_code == 400
    assert j['Code'] == -3
    assert j['Details'] == 'Parsing failed at pos 33, lineno 1, colno 34'


def test_new_simple(client):
    new_movies = {
        'Gardens of the Moon': ['Ganoes Paran', 'Whiskeyjack', 'Fiddler', 'Tattersail', 'Anomander Rake'], 'Deadhouse Gates': ['Fiddler', 'Cutter', 'Apsalar', 'Icarium', 'Mappo Runt']
    }

    r = client.post(api_new, json=new_movies)
    j = r.get_json()

    assert r.status_code == 201
    assert j['Results'] == []
    assert j['Description'] == 'All movies added successfully'

    # Also check that they were actually, functionally added
    r = client.get(api_arbitrary, query_string={
                   'target': 'Ganoes Paran', 'root': 'Icarium'})
    j = r.get_json()

    assert r.status_code == 200
    assert j['Results'] == [['Icarium', 'Ganoes Paran', 2]]
    assert j['Description'] == 'Success'


def test_new_invalid_json_simple(client):
    r = client.post(api_new, data='foobar')
    j = r.get_json()

    assert r.status_code == 400
    assert j['Code'] == -3
    assert j['Details'] == 'Parsing failed at pos 0, lineno 1, colno 1'


def test_new_invalid_json_complex(client):
    r = client.post(api_new, data='{ "foobar" : "muxqaz", "actor" : None }')
    j = r.get_json()

    assert r.status_code == 400
    assert j['Code'] == -3
    assert j['Details'] == 'Parsing failed at pos 33, lineno 1, colno 34'


def test_api_not_exist(client):
    r = client.get('/api/spacey-number')

    assert r.status_code == 404
