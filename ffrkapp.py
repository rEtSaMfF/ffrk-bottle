#!/usr/bin/env python3

import json
import os
import sys
import logging

from bottle import Bottle, redirect, request, response, TEMPLATE_PATH, error,\
    abort, static_file, BaseRequest, jinja2_view as view, Jinja2Template
from bottle.ext import sqlalchemy
from sqlalchemy import tuple_, func

from time import time

import models.models as models


### BOTTLE INIT START ###
app = application = Bottle()
app.debug = False

BaseRequest.MEMFILE_MAX = 1024 * 1024 * 2


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


@app.get('/dff/static/<filepath:path>', name='dff')
def dff(filepath):
    redirect(app.get_url('static', filepath=filepath), 301)


@app.get('/static/<filepath:path>', name='static')
def statics(filepath):
    root = 'static'
    for ext in ('js', 'css'):
        if filepath.endswith('.{}'.format(ext)):
            root = os.path.join(root, ext)
        if filepath.startswith('{}/'.format(ext)):
            filepath = filepath[len('{}/'.format(ext)):]
    '''
    # Commented out because image paths should be perfect for apache mod_wsgi
    for ext in ('png', ):
        subfolder = 'image'
        if filepath.endswith('.{}'.format(ext)):
            root = os.path.join(root, subfolder)
        if filepath.startswith('{}/'.format(subfolder)):
            filepath = filepath[len('{}/'.format(subfolder)):]
    '''
    logging.warning('Serving "{}" from the backend'.format(
        os.path.join(os.getcwd(), root, filepath)))
    return static_file(filepath, root=root)


@app.get('/robots.txt')
def robots():
    root = 'static'
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
        (('quest', 'quests'), models.Quest.frontend_columns),
        #(('character', 'characters'), models.Character.frontend_columns),
    ):
        if category in c:
            columns = cs
            break
    if not columns:
        abort(404, 'Unknown category "{}"'.format(category))
    context = {'rarity': rarity, 'category': category, 'columns': columns}

    try:
        return context
    except TemplateSyntaxError as e:
        logging.error('{}:{}'.format(e.filename, e.lineno))
        logging.error('exc_info=True', exc_info=True)
        abort(500, str(e))
    # Do we need an abort here?


@app.get('/character', name='character')
@app.get('/characters', name='characters')
@view('character.html')
def character():
    '''
    Render a character comparison
    '''
    context = {
        'o': models.Character,
        'data_url': '{}?category=character'.format(app.get_url('json'))
    }
    return context


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
        ('total_stamina', 'Stamina'),
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
    response.content_type = 'application/json; charset=UTF8'

    content = request.GET.get('content')
    event = request.GET.get('event')
    world_id = request.GET.get('world') or request.GET.get('world_id')
    dungeons = models.get_dungeons(content, event, world_id)

    outlist = []
    for dungeon in dungeons:
        row = dungeon.dict()
        row['world_name'] = '<a href="{}">{}</a>'.format(
            app.get_url('main', iden=dungeon.world_id),
            dungeon.world.name
        )
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
        conditions = dungeon.specific_conditions
        row['conditions'] = '<br>'.join(str(c) for c in conditions)
        outlist.append(row)

    if outlist:
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
             models.Material, models.Material.id, models.Material.id,
             False, None, None),
            (('ability', 'abilities'),
             models.Ability, models.Ability.name, models.Ability.name,
             False, None, None),
            (('enemy', 'enemies'),
             models.Enemy, models.Enemy.name, models.Enemy.enemy_id,
             True, None, None),
             #'name', True, None, None),
             #'enemy_id', True, None, None),
             #'param_id', True, None, None),
             # TODO 2015-05-18
             # Filter out blank names (or group such that the non-blanks win)
            (('relic', 'relics'),
             models.Relic, models.Relic.name, models.Relic.name,
             False, None, None),
            (('world', 'worlds'),
             models.World, models.World.id, models.World.id,
             True, None, None),
            (('dungeon', 'dungeons'),
             models.Dungeon, models.Dungeon.id, models.Dungeon.id,
             True, None, models.Dungeon.world_id),
            # TODO 2015-05-07
            # Enhance server-side pagination for Log
            # request.GET.get('offset', 0)
            # request.GET.get('limit', 25)
            (('log', 'logs'),
             models.Log, models.Log.timestamp.desc(), models.Log.id,
             True, 100, None),
            (('character', 'characters'),
             models.Character, models.Character.name, models.Character.buddy_id,
             True, None, models.Character.level),
            (('quest', 'quests'),
             models.Quest, models.Quest.id, models.Quest.id,
             True, None, None),
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
        if filter is not None and f is not None:
            # Filter Character by level
            if 'character' in c:
                q = q.filter(f <= filter)
            else:
                q = q.filter(f == filter)
        elif 'character' in c:
            # If we are not filtering Character by level
            # Then we want to return one row per buddy_id corresponding
            # to the highest level
            t = tuple_(models.Character.buddy_id, models.Character.level)
            sq = session.query(models.Character.buddy_id,
                               func.max(models.Character.level))\
                        .group_by(models.Character.buddy_id)
            q = q.filter(t.in_(sq))
        elif 'enemy' in c:
            # We want to ensure that the "main" param_id is returned
            #q = q.filter(models.Enemy.name != '')
            # This fails for "Sinspawn Gui" (4100101)

            # This fails for "Angler Whelk" (4060291)
            t = tuple_(models.Enemy.enemy_id, models.Enemy.param_id)
            sq = session.query(models.Enemy.enemy_id,
                               func.min(models.Enemy.param_id))\
                        .group_by(models.Enemy.enemy_id)
            q = q.filter(t.in_(sq))
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
