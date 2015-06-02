#!/usr/bin/env python3

import json
import os
import sys
import logging

from bottle import Bottle, redirect, request, response, TEMPLATE_PATH, error,\
    abort, static_file, BaseRequest, jinja2_view as view, Jinja2Template
from bottle.ext import sqlalchemy

from time import time
from wsgi import models


### BOTTLE INIT START ###
app = application = Bottle()
app.debug = False

BaseRequest.MEMFILE_MAX = 1024 * 1024 * 2

TEMPLATE_PATH.insert(0, os.path.join('wsgi', 'views'))


@app.error(500)
@app.error(403)
@app.error(404)
@view('404.html')
def error404(e):
    # e is a bottle.HTTPError
    return {'error': e.body}


Jinja2Template.defaults['url'] = app.get_url
Jinja2Template.defaults['get_active_events'] = models.get_active_events
Jinja2Template.defaults['get_content_dates'] = models.get_content_dates
### BOTTLE INIT END ###


def minify_json(data):
    '''
    Return a json string as small as possible.
    '''
    return json.dumps(data, default=models.default_encode, separators=(',',':'))

def save_json(data, filepath='/tmp/ffrk.json', min=False):
    logging.debug('Writing {}'.format(filepath))
    if min:
        kwargs={'separators': (',',':')}
    else:
        kwargs={'indent': 2}
    with open(filepath, 'w') as outfile:
        json.dump(data, outfile, sort_keys=True, ensure_ascii=True, **kwargs)


@app.get('/static/<filepath:path>', name='static')
def statics(filepath):
    root = os.path.join('wsgi', 'static')
    for ext in ('js', 'css'):
        if filepath.endswith('.{}'.format(ext)):
            root = os.path.join(root, ext)
        if filepath.startswith('{}/'.format(ext)):
            filepath = filepath[len('{}/'.format(ext)):]
    logging.warning('Serving "{}" from the backend'.format(
        os.path.join(os.getcwd(), root, filepath)))
    return static_file(filepath, root=root)


@app.get('/robots.txt')
def robots():
    root = os.path.join('wsgi', 'static')
    return static_file('robots.txt', root=root)


# 2015-05-20
# Do not change the url routes until we can use bottle.get_url() in models
#@app.get('/id/<iden>', name='main')
@app.get('/<iden>', name='main')
@view('main.html')
def main(iden=None):
    '''
    Render a page for a single object.
    Corresponds with url('json_id').
    '''
    try:
        iden = int(iden)
    except ValueError:
        o = models.get_by_name(iden)
    else:
        o = models.get_by_id(iden)

    if o is not None:
        context = {
            'o': o,
        }
        try:
            return context
        except TemplateSyntaxError as e:
            logging.error('{}:{}'.format(e.filename, e.lineno))
            logging.error('exc_info=True', exc_info=True)
    abort(404, 'Object "{}" not found'.format(iden))


# 2015-05-20
# Do not change the url routes until we can use bottle.get_url() in models
#@app.get('/<category>', name='home_dynamic')
@app.get('/', name='home')
@view('table.html')
def home(category=None):
    '''
    Render a table.
    Corresponds with url('json').
    '''
    # TODO 2015-05-06
    # Make a real home page
    # 2015-05-07
    # We have an about page at least
    if category is None:
        category = request.GET.get('category', '').lower()
    if not category:
        redirect(app.get_url('main', iden='about'))
    rarity = request.GET.get('rarity', 'all')
    columns = ()
    for c, cs in (
        (('material', 'materials'), models.Material.frontend_columns),
        (('enemy', 'enemies'), models.Enemy.frontend_columns),
        (('relic', 'relics'), models.Relic.frontend_columns),
        (('ability', 'abilities'), models.Ability.frontend_columns),
        (('world', 'worlds', 'realm', 'realms'), models.World.frontend_columns),
        (('log', 'logs'), models.Log.frontend_columns),
    ):
        if category in c:
            columns = cs
            break
    context = {'rarity': rarity, 'category': category, 'columns': columns}

    try:
        return context
    except TemplateSyntaxError as e:
        logging.error('{}:{}'.format(e.filename, e.lineno))
        logging.error('exc_info=True', exc_info=True)
        abort(500, str(e))
    # Do we need an abort here?


@app.get('/calc', name='calc')
@app.get('/calculator', name='calculator')
@view('calc.html')
def calc():
    '''
    Render a damange calculator.
    '''
    return {}

@app.get('/dungeon', name='dungeon')
@app.get('/dungeons', name='dungeons')
@view('dungeons.html')
def dungeons():
    '''
    Render a dungeon table listing.
    Corresponds with url('json_dungeons').
    '''
    content = request.GET.get('content', '')
    event = request.GET.get('event', '')
    world_id = request.GET.get('world', '') or request.GET.get('world_id', '')
    columns = (
        ('challenge_level', 'Difficulty'),
        ('world_name', 'Realm'),
        ('name', 'Name'),
        ('type', 'Type'),
        ('conditions',
         'Conditions <span data-container="body" data-toggle="tooltip" title="The non-specific conditions are not listed here." class="glyphicon glyphicon-info-sign" aria-hidden="true"></span>'),
        ('stamina', 'Stamina'),
        ('shards',
         'Shards <span data-container="body" data-toggle="tooltip" title="First Time Reward + Mastery Reward" class="glyphicon glyphicon-info-sign" aria-hidden="true"></span>'),
        ('prizes', 'Rewards'),
    )

    context = {'columns': columns, 'content': content,
               'event': event, 'world_id': world_id}
    try:
        return context
    except TemplateSyntaxError as e:
        logging.error('{}:{}'.format(e.filename, e.lineno))
        logging.error('exc_info=True', exc_info=True)
        abort(500, str(e))
    # Do we need an abort here?


@app.get('/dungeons.json', name='json_dungeons')
@app.get('/json/dungeons')
def json_dungeons():
    '''
    Get JSON for dungeon listings.
    '''
    # TODO 2015-05-18
    # Filter dungeons by release.
    # TODO 2015-05-18
    # Add menu item to filter dungeons by release.
    response.content_type = 'application/json; charset=UTF8'

    content = request.GET.get('content')
    event = request.GET.get('event')
    world_id = request.GET.get('world') or request.GET.get('world_id')
    dungeons = models.get_dungeons(content, event, world_id)

    if dungeons:
        outlist = []
        for dungeon in dungeons:
            row = dungeon.dict()
            row['world_name'] = dungeon.world.name
            row['type'] = models.DUNGEON_TYPE[dungeon.dungeon_type]
            shards = 0
            prizes = []
            for prize in dungeon.prizes:
                if prize.name == 'Stamina Shard':
                    shards += prize.count
                    continue
                if prize.drop_type != 'COMMON':
                    prizes.append('<a href="{}">{}</a>'.format(
                        app.get_url('main', iden=prize.search_id), prize))
                else:
                    prizes.append(str(prize))
            row['shards'] = shards
            row['prizes'] = '<br>'.join(prizes)
            row['stamina'] = 0
            # This is repeated three times
            conditions = []
            conditions_present = False
            all_conditions_present = True
            for battle in dungeon.battles:
                row['stamina'] += battle.stamina
                if not battle.conditions:
                    all_conditions_present = False
                for c in battle.conditions:
                    conditions_present = True
                    # Filter out the standard conditions
                    if c.condition_id not in (1001, 1002, 1004):
                        conditions.append(str(c))
            if not conditions_present:
                conditions.append(
                    'We have not imported any conditions for this dungeon.')
            elif not all_conditions_present:
                conditions.append(
                    'We are missing some conditions for this dungeon.')
            if row['stamina'] == 0:
                row['stamina'] = 'Unknown'
            row['conditions'] = '<br>'.join(conditions)
            outlist.append(row)
        return minify_json(outlist)

    response.status = 404
    return minify_json({'success':False, 'error':'No results found'})


@app.get('/json/<id:int>', name='json_id')
def get_json_by_id(id):
    '''
    Get JSON for an object (or all similar objects).
    '''
    response.content_type = 'application/json; charset=UTF8'

    all = request.GET.get('all', False)
    enemy = request.GET.get('enemy', False)
    r = models.get_by_id(id, all=all, enemy=enemy)

    if r:
        if hasattr(r, 'jsonify'):
            # This is a single object
            return r.jsonify()
        # We have a list of objects
        return minify_json([i.dict() for i in r])

    response.status = 404
    return minify_json({'success':False, 'error':'No results found'})


@app.get('/json', name='json')
def get_json():
    '''
    Get JSON for a category (table).
    '''
    response.content_type = 'application/json; charset=UTF8'

    category = request.GET.get('category', None)
    if category is None:
        response.status = 404
        return minify_json({'success':False, 'error':'Unknown category'})
    category = category.lower()

    rarity = request.GET.get('rarity', 'all').lower()
    with models.session_scope() as session:
        q = None
        # category, model, order_by, group_by, rarity, limit, filter
        for c, m, o, g, r, l, f in (
            (('material', 'materials'),
             models.Material, 'name', 'id', False, None, None),
            (('ability', 'abilities'),
             models.Ability, 'name', 'name', False, None, None),
            (('enemy', 'enemies'), models.Enemy, models.Enemy.name.desc(),
             #'name', True, None, None),
             'enemy_id', True, None, None),
             #'param_id', True, None, None),
             # TODO 2015-05-18
             # Filter out blank names (or group such that the non-blanks win)
            (('relic', 'relics'),
             models.Relic, 'name', 'name', False, None, None),
            (('world', 'worlds'), models.World, 'id', 'id', True, None, None),
            (('dungeon', 'dungeons'),
             models.Dungeon, 'id', 'id', True, None, models.Dungeon.world_id),
            # TODO 2015-05-07
            # Enhance server-side pagination for Log
            # request.GET.get('offset', 0)
            # request.GET.get('limit', 25)
            (('log', 'logs'),
             models.Log, models.Log.timestamp.desc(), 'id', True, 100, None),
        ):
            if category in c:
                q = session.query(m).order_by(o).group_by(g).limit(l)
                #q = session.query(models.Relic).filter(models.Relic.series_id.notlike(1)).group_by('name').order_by('name')
                if r:
                    rarity = 'all'
                break
        if q is None:
            response.status = 404
            return minify_json({'success':False, 'error':'Unknown category'})
        if rarity != 'all':
            # Some tables do not have a rarity column
            q = q.filter_by(rarity=rarity)
        filter = request.GET.get('filter')
        if filter is not None:
            q = q.filter(f == filter)
        q = q.all()
        if q:
            return minify_json([i.dict() for i in q])
        response.status = 404
        return minify_json({'success':False, 'error':'No results found'})


@app.post('/post', method='POST')
def post():
    '''
    Parse a new FFRK response (intercepted from a client).

    This is basically the same thing as ffrk_mitm.response() except that
    here we pick the proper function from the 'action' key instead of
    flow.request.path.
    '''
    #abort(401, '401 Unauthorized')
    response.content_type = 'application/json; charset=UTF8'
    try:
        data = request.json
        if data is None:
            response.status = 501
            return minify_json({'success':False, 'error':'No data'})

        action = data.get('action')
        if action is None:
            response.status = 501
            return minify_json({'success':False, 'error':'Unknown action'})

        filepath = os.path.join(
            os.environ.get('OPENSHIFT_DATA_DIR', '/tmp'),
            'post',
            '{}-{:0.0f}.json'.format(
                action.lstrip('/').replace('/', '_'),
                time()*1000000
            )
        )
        #save_json(data, filepath=filepath, min=True)
        #del (data['action'])
        for a, m in (
                ('get_battle_init_data', models.import_battle),
                ('/dff/world/battles', models.import_battle_list),
                ('/dff/world/dungeons', models.import_world),
                ('win_battle', models.import_win_battle),
        ):
            if action == a:
                if m(data=data, filepath=filepath):
                    return minify_json({'success': True})
                else:
                    response.status = 501
                    return minify_json({'success':False, 'error':'Bad data'})
        response.status = 501
        return minify_json({'success':False, 'error':'Unknown action'})
    except Exception as e:
        logging.error(e)
        logging.error('exc_info=True', exc_info=True)
        response.status = 500
        return minify_json(
            {
                'success':False,
                'error':'{}: {}'.format(str(e.__class__), str(e))
            }
        )


### EOF ###
