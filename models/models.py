from __future__ import absolute_import

import csv
import json
import logging
import os
import sys
import time
import traceback

import arrow

from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Boolean,\
    ForeignKey, Table, desc
from sqlalchemy_utils import ArrowType
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT
from sqlalchemy.orm import sessionmaker, load_only, relationship, backref,\
    joinedload, subqueryload, lazyload

from .base import BetterBase, session_scope, create_session, default_encode,\
    make_tables
from .ability import Ability, AbilityCost
from .battle import Battle
from .character import Character, CharacterEquip, CharacterAbility
from .condition import Condition, SpecificCondition
from .drop import Drop, DropAssociation
from .dungeon import Dungeon, DUNGEON_TYPE, get_content_dates, get_dungeons
from .enemy import Enemy, Attribute, AttributeAssociation
from .log import Log
from .material import Material
from .prize import Prize
from .quest import Quest, import_quests
from .relic import Relic
from .world import World, get_active_events


# TODO 2015-05-19
# Improve injection attack protection
# Basically escape every String column


### START CLASS DEFINITIONS ###


# Should this be BetterBase?
class About(object):
    name = 'About'

    main_panels = (
        {
            'title': 'About',
            'body': 'A FINAL FANTASY Record Keeper Database',
            #'items': ('items{}'.format(i) for i in range(5)),
            'footer': '*Work in progress<iframe src="https://ghbtns.com/github-btn.html?user=retsamff&amp;repo=ffrk-bottle&amp;type=fork&amp;count=true" scrolling="0" class="pull-right" frameborder="0" height="20px" width="100px"></iframe>',
        },
    )


### END CLASS DEFINITIONS ###


def get_realms():
    """Get an iterable of 2-tuples (series_id, name) of Realms."""
    r = ()
    with session_scope() as session:
        realms = session.query(World)\
                        .options(load_only(World.series_id, World.name))\
                        .filter(World.world_type == 1).all()
        session.expunge_all()
    r = [(w.series_id, w.name) for w in realms]
    return [(200001, 'Core')] + sorted(r) + [(150001, 'FFT')]


def get_load_data(data, filepath):
    """Get a dictionary of data or load the dictionary from a JSON file."""
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)
    return data


def byteify(input):
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


def import_battle_list(data=None, filepath=''):
    """/dff/world/battles"""
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

    #data = byteify(data)

    success = False
    with session_scope() as session:
        for battle in data['battles']:
            new_battle = session.query(Battle).filter_by(
                id=battle['id']).first()
            if new_battle is None:
                new_battle = Battle(**battle)
                session.add(new_battle)
                session.commit()
                # This will output None for the dungeon name :(
                new_log = Log(log='Create Battle({})'.format(new_battle))
                session.add(new_log)
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success


def import_world(data=None, filepath='', ask=False):
    """/dff/world/dungeons"""
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

    success = False
    with session_scope() as session:
        world = data['world']
        new_world = session.query(World).filter_by(id=world['id']).first()
        if new_world is None:
            new_world = World(**world)
            session.add(new_world)
            session.commit()
            new_log = Log(log='Create World({})'.format(new_world))
            session.add(new_log)
        for dungeon in data.get('dungeons', []):
            captures = dungeon['captures']
            prizes = dungeon['prizes']
            new_dungeon = session.query(Dungeon).filter_by(
                id=dungeon['id']).first()
            if new_dungeon is None:
                new_dungeon = Dungeon(**dungeon)
                session.add(new_dungeon)
                session.commit()
                new_log = Log(log='Create Dungeon({})'.format(new_dungeon))
                session.add(new_log)
            # Added with 2015-06-07 patch
            if new_dungeon.total_stamina == 0:
                new_dungeon.total_stamina = dungeon.get('total_stamina', 0)
                new_log = Log(
                    log='Update {}({}).total_stamina from 0 to {}'.format(
                        type(new_dungeon).__name__, new_dungeon,
                        new_dungeon.total_stamina
                    )
                )
                session.add(new_log)
                session.commit()
#            '''
            for capture in captures:
                # We want to create the Condition() when we import_world()
                # However we do not want to overwrite or duplicate an old
                # Condition()
                # But we also want to have the Condition.code_name and
                # Condition.condition_id
                # NOTE 2015-06-07
                # There is now a Condition.battle_specific_score_id
                for specific in capture['sp_scores']:
                    # So first get what is given
                    battle_id = specific['battle_id']
                    title = specific['title']
                    #print (title)
                    #print (type(title))
                    old_condition = session.query(SpecificCondition).filter(
                        SpecificCondition.battle_id == battle_id,
                        SpecificCondition.dungeon_id == new_dungeon.id,
                        SpecificCondition.title == title).first()
                    if old_condition is not None:
                        continue
                    new_condition = SpecificCondition(
                        dungeon_id=new_dungeon.id, **specific)
                    #print (u'{}'.format(new_condition))
                    new_log = Log(log=u'Create {}({})'.format(
                        type(new_condition).__name__,
                        new_condition))
                    session.add_all((new_condition, new_log))
                    #session.add(new_condition)
                    session.commit()
                    #old_battle = session.query(Battle).filter(
                    #    Battle.id == battle_id).first()
                    # But we actually are unable to associate the Condition()
                    # if the Battle() does not exist yet.
                    # It will not on the first run of import_world()
                    #if old_battle is None:
                    #    continue
                    # So I am commenting this feature out
#            '''
            for prize_type, prizes_list in prizes.items():
                for prize in prizes_list:
                    id = prize['id']
                    name = prize['name']
                    drop = session.query(Drop).filter_by(
                        id=id).first()
                    if drop is None:
                        drop = Drop(id=id, name=name)
                    prize['prize_type'] = prize_type
                    old_prize = session.query(Prize).filter_by(
                        drop_id=id, prize_type=prize_type,
                        dungeon=new_dungeon).first()
                    if old_prize is not None:
                        continue
                    prize['drop_id'] = id
                    new_prize = Prize(**prize)
                    new_prize.dungeon = new_dungeon
                    new_prize.drop = drop
                    session.add(new_prize)
                    session.commit()
                    new_log = Log(
                        log='Create Prize({}) from Dungeon({})'.format(
                            new_prize, new_dungeon))
                    session.add(new_log)
                    session.commit()
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success


def import_win_battle(data=None, filepath=''):
    """/dff/battle/win
    /dff/event/wday/9/win_battle
    """
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    data = get_load_data(data, filepath)

    battle_id = data.get('battle_id')
    if battle_id is None:
        logging.critical(
            'We do not have a battle_id to import this win_battle.')
        logging.critical('Skipping this import.')
        return False

    success = False
    with session_scope() as session:
        battle = session.query(Battle).filter_by(id=battle_id).first()
        if battle is None:
            logging.critical(
                'We are missing a battle object for {}.'.format(battle_id))
            logging.critical('Skipping this import.')
            return False

        score = data['result']['score']
        general = score['general']
        specific = score['specific']
        for s in general + specific:
            # Changed with 2015-06-07 patch
            # I just changed the title in the DB
            if s['title'] == "Times KO'd":
                s['title'] == "Characters KO'd"
            # Get the condition if it already exists
            old_condition = session.query(Condition).filter_by(
                title=s['title'], condition_id=s['id'], code_name=s['code_name']
            ).first()
            if old_condition is None:
                # Make a new condition if it does not exist yet
                old_condition = Condition(**s)
                session.add(old_condition)
                new_log = Log(
                    log=u'Create Condition({})'.format(old_condition))
                session.add(new_log)
                #new_condition = SpecificCondition(
                #    battle_id=battle_id,
                #    dungeon_id=battle.dungeon_id,
                #    title=s['title'])
                #session.add(new_condition)
                #session.commit()
            if old_condition not in battle.conditions:
                battle.conditions.append(old_condition)
                new_log = Log(log=u'Add Condition({}) to Battle({})'.format(
                    old_condition, battle))
                session.add(new_log)
                session.commit()
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success


def import_battle(data=None, filepath=''):
    """get_battle_init_data"""
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    data = get_load_data(data, filepath)

    success = False
    with session_scope() as session:
        battle = data['battle']
        battle_id = battle['battle_id']
        for round in battle['rounds']:
            for enemy in round['enemy']:
                for e in enemy['children']:
                    new_drops = []
                    for drop in e['drop_item_list']:
                        # Get/Create Drop()
                        id = drop.get('item_id')
                        if id is not None:
                            new_drop = session.query(Drop).filter_by(
                                id=id).first()
                            if new_drop is None:
                                name = get_name_by_id(id)
                                if name == id:
                                    name = None
                                new_drop = Drop(id=id, name=name)
                            new_drops.append(new_drop)
                    # Get/Create Enemy()
                    enemy_id = e['enemy_id']
                    params = e['params']
                    if isinstance(params, dict):
                        params = (params,)
                    for p in params:
                        param_id = p['id']
                        lv = p['lv']
                        # Ex bosses may have the same level as their Elite
                        # but have different stats
                        new_enemy = session.query(Enemy).filter_by(
                            param_id=param_id,
                            lv=lv,
                        ).first()
                        if new_enemy is None:
                            event = battle.get('event')
                            if isinstance(event, dict):
                                e['event_id'] = event.get('event_id')
                                e['event_type'] = event.get('event_type')
                            e['is_sp_enemy'] = enemy['is_sp_enemy']
                            e['params'] = p
                            new_enemy = Enemy(**e)
                            new_log = Log(
                                log=u'Create Enemy({})'.format(new_enemy))
                            session.add_all((new_enemy, new_log))
                            session.commit()
                        # Get/Create/Associate Attribute()
                        for attribute in p['def_attributes']:
                            attribute = {k:int(v) for k, v in attribute.items()}
                            new_attribute = session.query(Attribute).filter_by(
                                **attribute).first()
                            if new_attribute is None:
                                new_attribute = Attribute(**attribute)
                                new_log = Log(log='Create Attribute({})'.format(
                                    new_attribute))
                                session.add_all((new_attribute, new_log))
                                session.commit()
                            #if new_attribute not in new_enemy.attributes:
                            association = session.query(AttributeAssociation)\
                                .filter(
                                    AttributeAssociation.attribute_id == new_attribute.id,
                                    AttributeAssociation.param_id == new_enemy.param_id
                                ).first()
                            if association is None:
                                association = AttributeAssociation(
                                    attribute_id=new_attribute.id,
                                    param_id=new_enemy.param_id)
                                session.add(association)
                                session.commit()
                                # Ugh, this outputs None for the association
                                new_log = Log(
                                    log='Create AttributeAssociation({})'\
                                    .format(association))
                                session.add(new_log)
                                session.commit()
                                #new_enemy.attributes.append(new_attribute)
                                #new_log = Log(
                                #    log='Add Attribute({}) to Enemy({})'.format(
                                #        new_attribute, new_enemy))
                                #session.add(new_log)
                        # Get Battle() (or fail)
                        old_battle = session.query(Battle).filter_by(
                            id=battle_id).first()
                        if old_battle is None:
                            logging.warning(
                                u'We are missing a battle object for {}'\
                                .format(new_enemy))
                            # This may occur if we skip import_battle_list()
                            continue
                        # Associate Drop()
                        for new_drop in new_drops:
                            # See if we have a DropAssociation already
                            drop_association = session.query(
                                DropAssociation).filter_by(
                                    enemy_id=new_enemy.id,
                                    drop_id=new_drop.id,
                                    battle_id=old_battle.id,
                                ).first()
                            if drop_association is None or\
                               drop_association.battle_id != old_battle.id:
                                # We do not have a DropAssociation or
                                # the DropAssociation is different
                                # so make a new one
                                drop_association = DropAssociation(
                                    enemy_id=new_enemy.id,
                                    drop_id=new_drop.id,
                                    battle_id=old_battle.id,
                                )
                                session.add(new_drop)
                                session.add(drop_association)
                                session.commit()
                                new_log = Log(
                                    log='Create DropAssociation({})'.format(
                                        drop_association))
                                session.add(new_log)
                        # Associate Enemy() with Battle()
                        if old_battle not in new_enemy.battles:
                            new_enemy.battles.append(old_battle)
                            new_log = Log(
                                log=u'Add Enemy({}) to Battle({})'.format(
                                    new_enemy, old_battle))
                            session.add(new_log)
                        session.commit()
                        # TODO 2015-05-10
                        # Improve this nesting indentation.
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success


def create_fix_relic(e):
    success = False
    with session_scope() as session:
        new_relic = session.query(Relic).filter(
            Relic.equipment_id == e['equipment_id'],
            Relic.level == e['level'],
            Relic.rarity == e['rarity']
        ).first()
        if new_relic is None:
            new_relic = Relic(**e)
            new_log = Log(log='Create Relic({})'.format(new_relic))
            session.add_all((new_relic, new_log))
            session.commit()
        if new_relic.critical != e['critical']:
            new_relic.critical = e['critical']
            new_log = Log(log='Update {}({}).critical from 0 to {}'.format(
                type(new_relic).__name__, new_relic, new_relic.critical))
            session.add(new_log)
            session.commit()
        if not new_relic.image_path:
            new_relic.image_path = e['image_path']
            session.commit()
        if not new_relic.detail_image_path:
            new_relic.detail_image_path = e['detail_image_path']
            session.commit()
        success = True
    return success


def check_ssb(stat, buddy_id, old_value, new_value):
    """Check if the stat difference is due to the mastery of an SSB.

    Requires the values to be hard-coded in a local "ssb.csv" file with
    columns: buddy_id,name,stat,value

    Returns bool.
    """
    filepath = os.path.join(os.environ['OPENSHIFT_DATA_DIR'], 'ssb.csv')
    try:
        with open(filepath) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # continue if we do not have the correct buddy_id
                if int(row['buddy_id']) != int(buddy_id):
                    continue

                # Here we have the correct buddy_id
                # Check if we have the correct stat
                if not (row['stat'] == stat or
                        'series_{}'.format(row['stat']) == stat):
                    # return False because stat difference is not due to
                    # this SSB mastery.
                    # Is it possible in the future that a single character's SSB
                    # may include a stat boost to different stats?
                    # If so continue instead.
                    return False

                # Here we have the correct stat
                # Check if the stat difference is correct
                if int(row['value']) == (int(new_value) - int(old_value)):
                    # It appears as if the stat difference is due to a
                    # SSB mastery.
                    logging.debug(
                        'Stat difference due to SSB mastery for ' +
                        '{} found and ignored.'.format(row['name'])
                    )
                    return True
    except (FileNotFoundError, ):
        return False

    return False


def create_fix_character(c):
    success = False

    # Added with 2015-06-07 patch
    for k in c.keys():
        if k.startswith('sp_'):
            c[k.replace('sp_', 'series_')] = c[k]
            del(c[k])

    with session_scope() as session:
        new_character = session.query(Character).filter(
            Character.buddy_id == c['buddy_id'],
            Character.level == c['level']).first()

        if new_character is None:
            new_character = Character(**c)
            new_log = Log(log='Create {}({})'.format(
                type(new_character).__name__, new_character))
            session.add_all((new_character, new_log))
            session.commit()

        # Compare and update stats for balance patches.
        c['defense'] = c['def']
        for k in new_character.columns:
            if k in ('description', 'name', 'image_path', 'id'):
                continue
            old_value = new_character.__getattribute__(k)
            new_value = c[k]
            if old_value != new_value:
                # Check added with my first SSB on 2016-03-23
                if check_ssb(k, c['buddy_id'], old_value, new_value):
                    continue
                new_character.__setattr__(k, new_value)
                new_log = Log(log='Update {}({}).{} from {} to {}'.format(
                    type(new_character).__name__, new_character,
                    k, old_value, new_value)
                )
                session.add(new_log)
                session.commit()

        # Add what types of Relic and Ability this Character may use.
        # Ideally this would only run once per balance patch.
        for i, ec in c['equipment_category'].items():
            ce = session.query(CharacterEquip).filter(
                CharacterEquip.category_id == ec['category_id'],
                CharacterEquip.equipment_type == ec['equipment_type'],
                CharacterEquip.buddy_id == new_character.buddy_id).first()
            if ce is not None:
                continue
            ec['buddy_id'] = new_character.buddy_id
            ce = CharacterEquip(**ec)
            new_log = Log(
                log='Add {}({}) to {}({})'.format(
                    type(ce).__name__, ce,
                    type(new_character).__name__, new_character
                )
            )
            session.add_all((ce, new_log))
            session.commit()
        for i, ac in c['ability_category'].items():
            ca = session.query(CharacterAbility).filter(
                CharacterAbility.category_id == ac['category_id'],
                CharacterAbility.buddy_id == new_character.buddy_id).first()
            if ca is not None:
                if ca.rarity != int(ac['rarity']):
                    old_rarity = ca.rarity
                    ca.rarity = ac['rarity']
                    new_log = Log(
                        log='Update {} {}({}).rarity from {} to {}'.format(
                            new_character.name,
                            type(ca).__name__, ca,
                            old_rarity, ca.rarity
                        )
                    )
                    session.add(new_log)
                continue
            ac['buddy_id'] = new_character.buddy_id
            ca = CharacterAbility(**ac)
            new_log = Log(
                log='Add {}({}) to {}({})'.format(
                    type(ca).__name__, ca,
                    type(new_character).__name__, new_character))
            session.add_all((ca, new_log))
            session.commit()
        success = True
    return success


def import_party(data=None, filepath=''):
    """/dff/party/list"""
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    data = get_load_data(data, filepath)

    success = False
    with session_scope() as session:
        equipments = data['equipments']
        for e in equipments:
            create_fix_relic(e)

        materials = data['materials']
        for m in materials:
            if session.query(session.query(Material).filter_by(
                    id=m['id']).exists()).scalar():
                continue
            new_material = Material(**m)
            new_log = Log(log='Create Material({})'.format(new_material))
            session.add_all((new_material, new_log))
            session.commit()

        buddies = data['buddies']
        for c in buddies:
            create_fix_character(c)
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success


def import_dff(data=None, filepath=''):
    data = get_load_data(data, filepath)

    data['equipments'] = []
    data['materials'] = []
    data['buddies'] = data['buddy']

    return import_party(data, filepath)


def import_recipes(data=None, filepath=''):
    """/dff/ability/get_generation_recipes
    /dff/ability/get_upgrade_recipes
    """
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    data = get_load_data(data, filepath)

    success = False
    with session_scope() as session:
        recipes = data['recipe']
        for grades in recipes.values():
            for a in grades.values():
                new_ability = session.query(Ability).filter_by(
                    ability_id=a['ability_id'], grade=a['grade']).first()
                if new_ability is None:
                    new_costs = []
                    for material_id, count in\
                        a['material_id_2_num'].items():
                        with session.no_autoflush:
                            material = session.query(Material).filter_by(
                                id=material_id).one()
                        new_cost = AbilityCost(count=count)
                        new_cost.material = material
                        new_costs.append(new_cost)
                    new_ability = Ability(**a)
                    for new_cost in new_costs:
                        new_ability.materials.append(new_cost)
                    new_log = Log(log='Create Ability({})'.format(new_ability))
                    session.add_all((new_ability, new_log))
                    session.commit()
                elif new_ability.required_gil == 32767 and\
                new_ability.required_gil < a['required_gil']:
                    new_ability.required_gil = a['required_gil']
                    new_log = Log(
                        log='Update Ability({}).required_gil to {}'.format(
                            new_ability, new_ability.required_gil
                        )
                    )
                    session.add(new_log)
                    session.commit()
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success


def import_enhance_evolve(data=None, filepath=''):
    """/dff/equipment/enhance
    /dff/equipment/evolve
    """
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

    success = True
    for e in (data['old_src_user_equipment'],
              data['new_src_user_equipment'],):
        if not create_fix_relic(e):
            success = False
    return success


def import_grow(data=None, filepath=''):
    """/dff/grow_egg/use"""
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

    c = data['buddy']

    return create_fix_character(c)


def get_by_name(name, all=False):
    if name.lower() == 'about':
        return About()
    with session_scope() as session:
        # TODO 2015-05-12
        pass


def get_by_id(id, all=False, enemy=False):
    r = None
    if enemy:
        with session_scope() as session:
            # See Enemy.search_id for more information
            #(Enemy, Enemy.param_id, 'lv'),
            #(Enemy, Enemy.enemy_id, 'lv'),
            q = session.query(Enemy)\
                       .filter(Enemy.enemy_id == id)\
                       .order_by('lv')\
                       .options(subqueryload('*'))
            if all:
                r = q.all()
            else:
                r = q.first()
            session.expunge_all()
    if r is not None:
        return r

    with session_scope() as session:
        for m, c, o in (
            (Material, Material.id, ('id', )),
            (World, World.id, ('id', )),
            (Dungeon, Dungeon.id, ('id', )),
            (Ability, Ability.ability_id, ('name', )),
            (Relic, Relic.equipment_id, ('level', 'rarity')),
            (Battle, Battle.id, ('id', )),
            (Character, Character.buddy_id, ('level', )),
            (Quest, Quest.id, ('id', )),
            (Enemy, Enemy.param_id, ('lv', )),
        ):
            q = session.query(m)
            q = q.filter(c == id)
            for i in o:
                q = q.order_by(i)
            # joinedload('*') is slow
            #q = q.options(joinedload('*'))
            if m != World:
                q = q.options(subqueryload('*'))
            # lazyload('*') is the default and does not work the way I want
            #q = q.options(lazyload('*'))

            if all:
                r = q.all()
                if r:
                    break
            r = q.first()
            if r is not None:
                break
        session.expunge_all()
    return r


def get_name_by_id(id):
    with session_scope() as session:
        obj1 = session.query(Drop).filter_by(id=id).first()
        if obj1 is not None:
            if obj1.name:
                return obj1.name

    obj2 = get_by_id(id)
    if obj2 is not None:
        return obj2.name

    return id


### EOF ###
