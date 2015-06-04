#!/usr/bin/env python2

from __future__ import absolute_import

import decimal
import os
import sys
import json
import logging
import time
import traceback

import arrow

from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Boolean,\
    ForeignKey, Table, desc, event
from sqlalchemy.engine import Engine
from sqlalchemy.types import TIMESTAMP
from sqlalchemy_utils import ArrowType
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT
from sqlalchemy.ext.declarative import declarative_base as real_declarative_base
from sqlalchemy.orm import sessionmaker, load_only, relationship, backref,\
    joinedload, subqueryload, lazyload

from . import BetterBase, session_scope, create_session, default_encode
# TODO 2015-05-19
# Improve injection attack protection
# Basically escape every String column

"""
### SQLALCHEMY INIT START ###
declarative_base = lambda cls: real_declarative_base(cls=cls)

@declarative_base
class BetterBase(object):
    '''
    Add some default properties and methods to the SQLAlchemy declarative base.
    '''
    @property
    def columns(self):
        '''
        Return all of the columns.
        '''
        return (c.name for c in self.__table__.columns)
        #return (c.key for c in class_mapper(self.__class__).columns)

    @property
    def frontend_columns(self):
        '''
        The columns we see when listing all objects of this class.
        An iterable of tuples (attribute_name, display_name).
        '''
        return ((c, c) for c in self.columns)

    @property
    def main_columns(self):
        '''
        The columns we see when listing similar objects of this class.
        An iterable of tuples (attribute_name, display_name).
        Example: listing the stats per level.
        '''
        return self.frontend_columns

    @property
    def search_id(self):
        '''
        The id used to search for this object using get_by_id().
        This ignores varying attributes such as stats per level.
        '''
        # My *_tables do not have an id attribute so this is an AttributeError.
        return self.id

    _main_panels = None
    # Will be an iterable of dicts representing this object on its main page.

    def generate_main_panels(self):
        self._main_panels = []

    @property
    def main_panels(self):
        if self._main_panels is None:
            self.generate_main_panels()

        return self._main_panels

    extra_tabs = []
    # Will be an iterable of dicts representing differnet pages used to display
    # objects similar to this object but differing slightly
    # (such as stats per level).

    def __repr__(self):
        return u'{}({})'.format(self.__class__.__name__, self.columns)

    def dict(self):
        '''
        Transform the model into a dictionary.
        '''
        ret = dict((c, getattr(self, c)) for c in self.columns)
        if self.search_id is not None:
            ret['search_id'] = self.search_id
        return ret

    def jsonify(self):
        '''
        Transform the model into JSON.
        '''
        return json.dumps(self.dict(),
                          default=default_encode, separators=(',',':'))


def default_encode(obj):
    if isinstance(obj, decimal.Decimal):
        return u'{:.2f}'.format(self._value)
    if isinstance(obj, arrow.arrow.Arrow):
        return obj.for_json()
    if isinstance(obj, arrow.arrow.datetime):
        return arrow.get(obj).for_json()
        #return arrow.get(obj).timestamp
        #if obj.utcoffset() is not None:
        #    obj = obj - obj.utcoffset()

        #obj = obj.replace(tzinfo=None)
        #return (obj - arrow.arrow.datetime(1970, 1, 1)).total_seconds()
    raise TypeError('{} is not JSON serializable'.format(obj))


engine = create_engine(
    'mysql+pymysql://{}:{}@{}:{}/{}'.format(
        os.environ['OPENSHIFT_MYSQL_DB_USERNAME'],
        os.environ['OPENSHIFT_MYSQL_DB_PASSWORD'],
        os.environ['OPENSHIFT_MYSQL_DB_HOST'],
        os.environ['OPENSHIFT_MYSQL_DB_PORT'],
        'ffrk',
    ), pool_recycle=3600)
create_session = sessionmaker(bind=engine)


# I do not use this plugin
'''
plugin = sqlalchemy.Plugin(
    engine,
    #Base.metadata,
    BetterBase.metadata,
    keyword='db',
    create=True,
    commit=True,
    use_kwargs=False
)
'''


@contextmanager
def session_scope():
    '''
    Provide a transactional scope around a series of operations.
    '''
    session = create_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(e, e.args)
        logging.error(traceback.print_exc())
        logging.error('exc_info=True', exc_info=True)
    finally:
        session.close()


# TODO 2015-05-08
# aaargh this
if False:
#if True:
    logging.basicConfig()
    logger = logging.getLogger('ffrk.sqltime')
    logger.setLevel(logging.DEBUG)

    @event.listens_for(Engine, 'before_cursor_execute')
    def before_cursor_execute(conn, cursor, statement,
                              parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
        logger.debug('Start Query: {}'.format(statement))

    @event.listens_for(Engine, 'after_cursor_execute')
    def after_cursor_execute(conn, cursor, statement,
                             parameters, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop(-1)
        logger.debug('Query Complete!')
        logger.debug('Total Time: {:f}'.format(total))


def make_tables():
    BetterBase.metadata.create_all(engine)
create_tables = make_tables
### SQLALCHEMY INIT END ###
"""

# 2015-04-28 not used now
'''
def to_roman(n):
    digits = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD' ),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]
    result = ''
    while digits:
        val, romn = digits[0]
        if n < val:
            digits.pop(0)
        else:
            n -= val
            result += romn
    return result
'''

STRFTIME = '%Y-%m-%dT%H:%M:%S%z (%Z)'

CATEGORY_ID = {
    'Dagger': 1,
    'Sword': 2,
    'Katana': 3,
    'Axe': 4,
    'Hammer': 5,
    'Spear': 6,
    'Fist': 7,
    'Rod': 8,
    'Staff': 9,
    'Bow': 10,
    'Instrument': 11,
    'Whip': 12,
    'Thrown': 13,
    'Book': 14,

    'Ball': 30,

    'Shield': 50,
    'Hat': 51,
    'Helm': 52,
    'Light Armor': 53,
    'Armor': 54,
    'Robe': 55,
    'Bracer': 56,

    'Accessory': 80,

    'Weapon Upgrade': 98,
    'Armor Upgrade': 99,

    'Black Magic': 1,
    'White Magic': 2,
    'Summoning': 3,
    'Spellblade': 4,
    'Combat': 5,
    'Support': 6,
    'Celerity': 7,
    'Dragoon': 8,
    'Monk': 9,
    'Thief': 10,
    'Knight': 11,
    'Samurai': 12,
    'Ninja': 13,
}

ABILITY_ID_NAME = {
    1: 'Black Magic',
    2: 'White Magic',
    3: 'Summoning',
    4: 'Spellblade',
    5: 'Combat',
    6: 'Support',
    7: 'Celerity',
    8: 'Dragoon',
    9: 'Monk',
    10: 'Thief',
    11: 'Knight',
    12: 'Samurai',
    13: 'Ninja',
}

EQUIP_ID_NAME = {}
for k, v in CATEGORY_ID.items():
    if ABILITY_ID_NAME.get(v) == k:
        continue
    EQUIP_ID_NAME[v] = k

WEAPON = 1
ARMOR = 2
ACCESSORY = 3


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


class CharacterEquip(BetterBase):
    __tablename__ = 'character_equip'
    category_id = Column(TINYINT, primary_key=True, autoincrement=False)
    equipment_type = Column(TINYINT, primary_key=True, autoincrement=False)
    buddy_id = Column(Integer, primary_key=True, autoincrement=False)

    def __init__(self, **kwargs):
        known_factor = '100'
        if kwargs['factor'] != known_factor:
            logging.critical(
                '{} has a non {} factor'.format(
                    type(self).__name__, known_factor))
        for i in (
            'factor',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(CharacterEquip, self).__init__(**kwargs)

    def __repr__(self):
        return '{}'.format(
            EQUIP_ID_NAME.get(
                self.category_id,
                'Unknown EquipmentCategory[{}]'.format(self.category_id)
            )
        )

class CharacterAbility(BetterBase):
    __tablename__ = 'character_ability'
    category_id = Column(TINYINT, primary_key=True, autoincrement=False)
    rarity = Column(TINYINT, nullable=False)
    buddy_id = Column(Integer, primary_key=True, autoincrement=False)

    def __init__(self, **kwargs):
        for i in (
            'name',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(CharacterAbility, self).__init__(**kwargs)

    def __repr__(self):
        return '[{}*] {}'.format(
            self.rarity,
            ABILITY_ID_NAME.get(
                self.category_id,
                'Unknown AbilityCategory[{}]'.format(self.category_id)
            )
        )

class Character(BetterBase):
    __tablename__ = 'character'
    id = Column(Integer, primary_key=True, autoincrement=True)
    buddy_id = Column(Integer, nullable=False)
    name = Column(String(length=32), nullable=False)
    job_name = Column(String(length=32), nullable=False)
    description = Column(String(length=256), nullable=False)
    series_id = Column(Integer, nullable=False)
    image_path = Column(String(length=64), nullable=False)

    level = Column(TINYINT, nullable=False)
    #level_max = Column(TINYINT, nullable=False)

    hp = Column(SMALLINT, nullable=False)
    atk = Column(SMALLINT, nullable=False)
    defense = Column(SMALLINT, nullable=False)
    acc = Column(SMALLINT, nullable=False)
    eva = Column(SMALLINT, nullable=False)
    matk = Column(SMALLINT, nullable=False)
    mdef = Column(SMALLINT, nullable=False)
    mnd = Column(SMALLINT, nullable=False)
    spd = Column(SMALLINT, nullable=False)

    series_hp = Column(SMALLINT, nullable=False)
    series_atk = Column(SMALLINT, nullable=False)
    series_def = Column(SMALLINT, nullable=False)
    series_acc = Column(SMALLINT, nullable=False)
    series_eva = Column(SMALLINT, nullable=False)
    series_matk = Column(SMALLINT, nullable=False)
    series_mdef = Column(SMALLINT, nullable=False)
    series_mnd = Column(SMALLINT, nullable=False)
    series_spd = Column(SMALLINT, nullable=False)

    frontend_columns = (
        ('image_path', 'Image'),
        ('name', 'Name'),
        ('series_id', 'Series'),
    )

    main_columns = (
        ('level', 'Level'),
        ('hp', 'HP'),
        ('atk', 'ATK'),
        ('defense', 'DEF'),
        ('acc', 'ACC'),
        ('eva', 'EVA'),
        ('matk', 'MAG'),
        ('mdef', 'RES'),
        ('mnd', 'MIND'),
        ('spd', 'SPD'),
        ('series_acc', 'RS ACC'),
        ('series_atk', 'RS ATK'),
        ('series_def', 'RS DEF'),
        ('series_eva', 'RS EVA'),
        ('series_matk', 'RS MAG'),
        ('series_mdef', 'RS RES'),
        ('series_mnd', 'RS MIND'),
    )

    @property
    def search_id(self):
        return self.buddy_id

    @property
    def extra_tabs(self):
        return (
            {
                'id': 'stats',
                'title': 'Stats by Level',
                'search_id': self.search_id,
                'columns': self.main_columns,
            },
        )

    def generate_main_panels(self):
        main_stats = []
        for k, v in (
            ('job_name', 'Class'),
            ('series_id', 'Series'),
        ):
            main_stats.append('{}: {}'.format(v, self.__getattribute__(k)))
        self._main_panels = (
            {
                'title': self.name,
                'body': '<a href="{0}"><img src="{0}" alt="{1}" title="{1}" class="img-responsive center-block"></a>'.format(
                    self.image_path, self.name),
                'items': main_stats,
            },
            {
                'title': 'Equipment',
                'items': self.get_equips(),
            },
            {
                'title': 'Abilities',
                'items': self.get_abilities(),
            },
        )

    def get_abilities(self):
        abilities = ()
        with session_scope() as session:
            abilities = session.query(CharacterAbility).filter(
                CharacterAbility.buddy_id == self.buddy_id).all()
            session.expunge_all()
        return abilities

    def get_equips(self):
        equips = ()
        with session_scope() as session:
            equips = session.query(CharacterEquip).filter(
                CharacterEquip.buddy_id == self.buddy_id).all()
            session.expunge_all()
        return equips

    def __init__(self, **kwargs):
        self.defense = kwargs['def']
        self.description = kwargs['description'].encode(
            sys.stdout.encoding, errors='ignore')
        if kwargs['job_name'] == 'Keeper':
            self.name = 'Tyro'
        else:
            self.name = kwargs['name']
        self.image_path = kwargs['image_path'].replace('/dff', '')

        for i in (
            'def',
            'description',
            'name',

            'id',
            'ability_1_id',
            'ability_2_id',
            'accessory_id',
            'weapon_id',
            'armor_id',
            'created_at',
            'exp',
            'row',
            'soul_strike_id',
            'image_path',

            'default_soul_strike_id',
            'ability_category',
            'equipment_category',
            'level_max',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Character, self).__init__(**kwargs)

    def __repr__(self):
        return '{} ({})'.format(self.name, self.level)


class Log(BetterBase):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(TIMESTAMP,
                       default=arrow.arrow.datetime.utcnow, nullable=False)
    log = Column(String(length=256), nullable=False)
    # I want a way to reference the objects in this log but that is not too easy

    frontend_columns = (
        ('timestamp', 'Timestamp'),
        ('log', 'Log'),
    )

    search_id = None

    def __init__(self, **kwargs):
        super(Log, self).__init__(**kwargs)
        logging.info(self.log)

    def __repr__(self):
        return '{} {}'.format(self.timestamp, self.log)


WORLD_TYPE = {
    1: 'Realm',
    2: 'Challenge',
}


class World(BetterBase):
    __tablename__ = 'world'
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(length=32), nullable=False)

    series_id = Column(Integer, nullable=False)
    opened_at = Column(ArrowType, nullable=False)
    # Worlds_1.opened_at = 2014-05-01T06:00:00+00:00
    closed_at = Column(ArrowType, nullable=False)
    kept_out_at = Column(ArrowType, nullable=False)
    world_type = Column(TINYINT, nullable=False)

    dungeons = relationship('Dungeon', backref='world')

    frontend_columns = (
        ('name', 'Name'),
        ('series_id', 'Series'),
        ('opened_at', 'Opened at'),
        ('kept_out_at', 'Kept out at'),
        # TODO 2015-05-11
        # Format and highlight open/closed events
    )

    @property
    def extra_tabs(self):
        return (
            {
                'id': 'dungeons',
                'title': 'Dungeons',
                # This should use a Bottle().get_url()
                #'data_url': '/json?category=dungeon&filter={}'.format(
                #    self.search_id),
                'data_url': '/dungeons.json?world_id={}'.format(
                    self.search_id),
                #'search_id': self.search_id,
                'columns': (
                    ('challenge_level', 'Difficulty'),
                    #('world_name', 'Realm'),
                    ('name', 'Name'),
                    ('type', 'Type'),
                    ('conditions',
                     'Conditions <span data-container="body" data-toggle="tooltip" title="The non-specific conditions are not listed here." class="glyphicon glyphicon-info-sign" aria-hidden="true"></span>'),
                    ('stamina', 'Stamina'),
                    ('shards',
                     'Shards <span data-container="body" data-toggle="tooltip" title="First Time Reward + Mastery Reward" class="glyphicon glyphicon-info-sign" aria-hidden="true"></span>'),
                    ('prizes', 'Rewards'),
                ),
                #'columns': (
                #       ('challenge_level', 'Difficulty'),
                #       ('name', 'Name'),
                #       ('dungeon_type', 'Dungeon Type'),
                #   ),
            },
        )

    def generate_main_panels(self):
        main_stats = []
        for k, v in self.frontend_columns:
            attr = self.__getattribute__(k)
            if isinstance(attr, (arrow.arrow.Arrow, arrow.arrow.datetime)):
                main_stats.append(
                    '{}: <abbr title="{}" data-livestamp="{}"></abbr>'.format(
                        v,
                        attr.strftime(STRFTIME),
                        attr
                    )
                )
            else:
                main_stats.append('{}: {}'.format(v, attr))

        now = arrow.now()
        if now < self.opened_at:
            main_stats.append(
                '{} will be available <abbr title="{}" data-livestamp="{}"></abbr>.'\
                .format(
                    WORLD_TYPE[self.world_type],
                    self.opened_at.strftime(STRFTIME),
                    self.opened_at
                )
            )
        if now > self.closed_at:
            # All events seem to close_at three days after we are kept_out_at
            # even though there is no redemption period for "challenge" types
            main_stats.append(
                '{} closed <abbr title="{}" data-livestamp="{}"></abbr>.'\
                .format(
                    WORLD_TYPE[self.world_type],
                    self.closed_at.strftime(STRFTIME),
                    self.closed_at
                )
            )
        if now < self.kept_out_at and self.world_type == 2:
            main_stats.append(
                '{} will end <abbr title="{}" data-livestamp="{}"></abbr>.'\
                .format(
                    WORLD_TYPE[self.world_type],
                    self.kept_out_at.strftime(STRFTIME),
                    self.kept_out_at
                )
            )

        self._main_panels = (
            {
                'title': 'Main Stats',
                'items': main_stats,
                #'footer': '<span class="glyphicon glyphicon-asterisk" aria-hidden="true"></span>Local time zones to be implemented.',
            },
        )

    def __init__(self, **kwargs):
        self.world_type = kwargs['type']
        #kwargs['opened_at'] = datetime.fromtimestamp(kwargs['opened_at'])
        #kwargs['closed_at'] = datetime.fromtimestamp(kwargs['closed_at'])
        #kwargs['kept_out_at'] = datetime.fromtimestamp(kwargs['kept_out_at'])
        kwargs['opened_at'] = arrow.get(kwargs['opened_at'])
        kwargs['closed_at'] = arrow.get(kwargs['closed_at'])
        kwargs['kept_out_at'] = arrow.get(kwargs['kept_out_at'])
        for i in (
            'bgm',
            'door_image_path',
            'has_new_dungeon',
            'image_path',
            'is_unlocked',
            'type',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(World, self).__init__(**kwargs)

    def __repr__(self):
        return '[{}] {}'.format(WORLD_TYPE[self.world_type], self.name)

def get_active_events(now=None):
    '''
    Return an iterable of the current active events.

    May return events active at the optional now kwarg datetime.
    '''

    events = []
    with session_scope() as session:
        q = session.query(World)\
                   .filter(World.world_type == 2)\
                   .order_by(World.opened_at)

        if now is None:
            now = arrow.now()

        events = q.filter(World.opened_at <= now)\
                  .filter(World.closed_at > now).all()
        session.expunge_all()
    return events

PRIZE_TYPE = {
    1: 'Completion Reward',
    2: 'First Time Reward',
    3: 'Mastery Reward',
}

class Prize(BetterBase):
    __tablename__ = 'prize'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=32), nullable=False)
    prize_type = Column(TINYINT, nullable=False)
    count = Column(Integer, nullable=False)

    drop_type = Column(String(length=16), nullable=False)
    drop_id = Column(Integer, ForeignKey('drop.id'), nullable=False)
    dungeon_id = Column(Integer, ForeignKey('dungeon.id'), nullable=False)

    drop = relationship('Drop', backref=backref('prizes'))
    dungeon = relationship('Dungeon',
                           backref=backref('prizes',
                                           order_by='Prize.prize_type'))

    @property
    def search_id(self):
        return self.drop_id

    def __init__(self, **kwargs):
        kwargs['count'] = kwargs['num']
        kwargs['drop_type'] = kwargs['type_name']
        for i in (
            'id',
            'num',
            'image_path',
            'type_name',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Prize, self).__init__(**kwargs)

    def __repr__(self):
        return '{} x{} ({})'.format(self.name, self.count,
                                    PRIZE_TYPE[self.prize_type])


# TODO 2015-05-11
# Replace dungeon_type column with a String?
DUNGEON_TYPE = {
    1: 'Classic',
    2: 'Elite',
}

class Dungeon(BetterBase):
    __tablename__ = 'dungeon'
    id = Column(Integer, primary_key=True, autoincrement=False)
    world_id = Column(Integer, ForeignKey('world.id'), nullable=False)
    series_id = Column(Integer, nullable=False)
    name = Column(String(length=64), nullable=False)
    dungeon_type = Column(TINYINT, nullable=False)
    challenge_level = Column(SMALLINT, nullable=False)

    opened_at = Column(ArrowType, nullable=False)
    # Dungeons_1.opened_at = 2014-05-01T06:00:00+00:00
    # Dungeons_2.opened_at = 2014-01-01T06:00:00+00:00
    # Dungeons_3.opened_at = 2014-09-17T03:00:00+00:00
    closed_at = Column(ArrowType, nullable=False)
    prologue = Column(String(length=1024), nullable=True)
    epilogue = Column(String(length=1024), nullable=True)

    battles = relationship('Battle', backref='dungeon')

    frontend_columns = (
        ('challenge_level', 'Difficulty'),
        ('name', 'Name'),
        ('dungeon_type', 'Dungeon Type'),
    )

    def generate_main_panels(self):
        main_stats = []
        for k, v in self.frontend_columns:
            main_stats.append('{}: {}'.format(v, self.__getattribute__(k)))
        #main_stats.append(
        main_stats[-1] =\
            'Dungeon Type: {}'.format(DUNGEON_TYPE[self.dungeon_type])
#        )
        main_stats.insert(0, '<a href="/{}">{}</a>'.format(
            self.world.search_id, self.world))
        # TODO 2015-05-11
        # Copy the opened_at/closed_at items from World?

        self._main_panels = [
            {
                'title': 'Main Stats',
                'items': main_stats,
            },
            {
                'title': 'Prologue',
                'body': self.prologue,
            },
        ]
        # Daily dungeons do not have a prologue
        if self.epilogue:
            self._main_panels.append(
                {
                    'title': 'Epilogue',
                    #'body': self.epilogue,
                    'body': 'spoilers',
                    # TODO 2015-05-11
                    'footer': 'Add markup with spoiler protection',
                }
            )
        battles = []
        total_stam = 0
        # This is repeated three times
        conditions = []
        conditions_count = 0
        all_conditions_present = True
        # TODO 2015-05-18
        # Put battles in tabs
        for battle in self.battles:
            item = '<a href="/{}">{} ({} round(s)) [{} stamina]</a>'.format(
                battle.search_id, battle.name,
                battle.round_num, battle.stamina)
            if battle.has_boss:
                item = '<strong>{}</strong>'.format(item)
            battles.append(item)
            total_stam += battle.stamina
            if not battle.conditions:
                all_conditions_present = False
            for c in battle.conditions:
                conditions_count += 1
                # Filter out the standard conditions
                if c.condition_id not in (1001, 1002, 1004):
                    conditions.append(str(c))

        self._main_panels[0]['items'].append(
            'Total stamina required: {}'.format(total_stam))

        conditions_body = None
        if not all_conditions_present:
            if conditions_count:
                conditions_body = 'We are missing some conditions for this dungeon.'
            else:
                conditions_body = 'We have not imported any conditions for this dungeon.'
        elif not conditions:
            conditions_body = 'There are no specific conditions for this dungeon.'

        self._main_panels.append(
            {
                'title': 'Specific Conditions',
                'body': conditions_body,
                'items': conditions,
                'footer': 'You may lose a max of {} medals and still achieve mastery for this dungeon.'.format(conditions_count//2) if all_conditions_present else '',
            }
        )

        self._main_panels.append(
            {
                'title': 'Battles',
                'items': battles,
                'footer': 'Bold battle name indicates a boss.',
            },
        )
        self._main_panels.append(
            {
                'title': 'Prizes',
                'items': ('<a href="/{}">{}</a>'.format(prize.search_id, prize)
                          if prize.drop_type != 'COMMON' else
                          '{}'.format(prize) for prize in self.prizes),
                # Maybe make the items accordian expand or at least group
                # visually by prize.drop_type
                'footer': 'The "Completion Reward" may be obtained multiple times.',
            },
        )
        self._main_panels.append(
            {
                'title': 'Enemies',
                #'items': ('<a href="/{}">{}</a>'.format(enemy.search_id, enemy) for enemy in self.enemies),
                'footer': '*To be implemented (maybe).',
            },
        )
        self._main_panels.append(
            {
                'title': 'Drops',
                #'items': ('<a href="/{}">{} from {}</a>'.format(drop.drop_id, drop.drop.name, drop.enemy) for drop in self.drops),
                #'footer': 'These locations are not all inclusive and the drop rates may vary.',
                'footer': '*To be implemented (maybe).',
            },
        )

    def __init__(self, **kwargs):
        kwargs['dungeon_type'] = kwargs['type']
        #kwargs['opened_at'] = datetime.fromtimestamp(kwargs['opened_at'])
        #kwargs['closed_at'] = datetime.fromtimestamp(kwargs['closed_at'])
        kwargs['opened_at'] = arrow.get(kwargs['opened_at'])
        kwargs['closed_at'] = arrow.get(kwargs['closed_at'])
        kwargs['epilogue'] = kwargs['epilogue'].encode(
            sys.stdout.encoding, errors='ignore')
        kwargs['prologue'] = kwargs['prologue'].encode(
            sys.stdout.encoding, errors='ignore')
        for i in (
            'background_image_path',
            'rank',
            'order_no',
            'is_new',
            'is_unlocked',
            'is_clear',
            'is_master',
            'bgm',
            'prologue_image_path',
            'epilogue_image_path',
            'prizes',
            'type',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Dungeon, self).__init__(**kwargs)

    def __repr__(self):
        return '{}/{} ({}) [{}]'.format(
            self.world, self.name,
            DUNGEON_TYPE[self.dungeon_type], self.challenge_level)

def find_dungeons_with_no_battles():
    '''
    Output which dungeons have no battles in our database for re-population.
    '''
    with session_scope() as session:
        dungeons = session.query(Dungeon).filter(~Dungeon.battles.any()).all()
        for dungeon in dungeons:
            logging.warning('{} has no battles'.format(dungeon))

def find_battles_with_no_conditions(boss=False):
    '''
    Output which battles have no conditions.
    '''
    # TODO 2015-05-29
    # Output boss battles with only 3 conditions.
    with session_scope() as session:
        battles = session.query(Battle)\
                         .filter(~Battle.conditions.any())
        for battle in battles.all():
            logging.warning('{} has no conditions'.format(battle.id))

def get_content_dates(event=None):
    '''
    Return an iterable of the main content update dates.
    '''
    dates = ()
    with session_scope() as session:
        world_query = session.query(World)
        if event:
            worlds = world_query.filter(World.world_type == 2)
        else:
            worlds = world_query.filter(World.world_type == 1)
        world_ids = (i.id for i in worlds)
        dungeons = session.query(Dungeon)\
                          .filter(Dungeon.world_id.in_(world_ids))\
                          .options(load_only(Dungeon.opened_at))\
                          .order_by(Dungeon.opened_at)\
                          .group_by(Dungeon.opened_at).all()
        # List not generator because I need the length
        dates = [d.opened_at for d in dungeons]
        session.expunge_all()
    return dates

def get_dungeons(content=None, event=None, world_id=None):
    '''
    Return an iterable of dungeons corresponding to a main content update.

    A content of 1 (or less) will return all dungeons.
    A null content or content greater than the number of content patches will
    return the latest batch only.
    '''
    try:
        world_id = int(world_id)
    except (ValueError, TypeError):
        world_id = None
    if world_id is not None:
        dungeons = ()
        with session_scope() as session:
            # DetachedInstanceError
            #world = session.query(World).filter(World.id == world_id).one()
            #dungeons = world.dungeons
            dungeons = session.query(Dungeon)\
                       .options(subqueryload(Dungeon.world))\
                       .options(subqueryload(Dungeon.prizes))\
                       .options(subqueryload(Dungeon.battles))\
                       .filter(Dungeon.world_id == world_id)\
                       .order_by(Dungeon.challenge_level, Dungeon.id).all()
            session.expunge_all()
        return dungeons

    if content == 'all':
        content = 0
    if content == 'latest':
        content = sys.maxsize
    try:
        content = int(content)
    except (ValueError, TypeError):
        content = sys.maxsize

    dungeons = []
    with session_scope() as session:
        worlds = session.query(World)
        if event:
            worlds = worlds.filter(World.world_type == 2)
        else:
            worlds = worlds.filter(World.world_type == 1)
        world_ids = (i.id for i in worlds)

        # This selects all the dungeons in an event or world
        dungeon_query = session.query(Dungeon)\
                               .options(subqueryload(Dungeon.world))\
                               .options(subqueryload(Dungeon.prizes))\
                               .options(subqueryload(Dungeon.battles))\
                               .filter(Dungeon.world_id.in_(world_ids))

        if content <= 1:
            # We want all the dungeons from the beginning
            dungeons = dungeon_query.all()
        else:
            # else we want to start from a specific content update
            # Get the dates dungeons were opened_at
            dates = get_content_dates(event=event)
            # If someone is asking for content from the future return the
            # latest content update only
            content = min(content, len(dates))
            # Subtract one from the content number because we count the original
            # content as "1" and not "0", also avoid IndexError
            content -= 1
            # Get the datetime this update was released
            opened_at = dates[content]
            # Now we can finally get all the dungeons released after this time
            dungeons = dungeon_query.filter(
                Dungeon.opened_at >= opened_at)\
                .order_by(Dungeon.challenge_level, Dungeon.id).all()
        session.expunge_all()
    return dungeons


condition_table = Table('condition_table', BetterBase.metadata,
                    Column('battle_id', Integer,
                           ForeignKey('battle.id'), nullable=False),
                    Column('condition_id', Integer,
                           ForeignKey('condition.id'), nullable=False)
)

class Condition(BetterBase):
    __tablename__ = 'condition'
    id = Column(Integer, primary_key=True, autoincrement=True)
    condition_id = Column(SMALLINT, nullable=False)
    code_name = Column(String(length=32), nullable=False)
    title = Column(String(length=128), nullable=False)
    #medal_num = Column(TINYINT, nullable=False)

    battles = relationship('Battle',
                           secondary=condition_table,
                           backref=backref('conditions', lazy='subquery'))

    def __init__(self, **kwargs):
        kwargs['condition_id'] = kwargs['id']
        for i in (
            'id',
            'medal_num',
        ):
            if i in kwargs:
                del(kwargs[i])

        super(Condition, self).__init__(**kwargs)

    def __repr__(self):
        return self.title


enemy_table = Table('enemy_table', BetterBase.metadata,
                    Column('enemy_id', Integer,
                           ForeignKey('enemy.id'), nullable=False),
                    Column('battle_id', Integer,
                            ForeignKey('battle.id'), nullable=False),
)

class Battle(BetterBase):
    __tablename__ = 'battle'
    id = Column(Integer, primary_key=True, autoincrement=False)
    dungeon_id = Column(Integer, ForeignKey('dungeon.id'), nullable=False)
    name = Column(String(length=64), nullable=False)
    round_num = Column(TINYINT, nullable=False)
    has_boss = Column(Boolean, nullable=False)
    stamina = Column(TINYINT, nullable=False)

    # TODO 2015-05-22
    # sort by Enemy.is_sp_enemy
    enemies = relationship('Enemy', secondary=enemy_table, backref='battles')

    # TODO 2015-05-19
    #messages = a many-to-many backref

    def generate_main_panels(self):
        main_stats = []

        self._main_panels = [
            {
                'title': 'Main Stats',
                'items': main_stats + [
                    'Name: {}'.format(self.name),
                    'Dungeon: {}'.format(
                        '<a href="/{}">{}</a>'.format(
                            self.dungeon.search_id,
                            str(self.dungeon),
                            #self.dungeon.name,
                        )
                    ),
                    'Round(s): {}'.format(self.round_num),
                    'Stamina: {}'.format(self.stamina),
                ],
            },
        ]

        if self.has_boss:
            self._main_panels.append(
                {
                    'title': 'Boss',
                    'footer': '*To be implemented (maybe).',
                }
            )

        # This is repeated three times
        conditions = []
        conditions_count = 0
        for c in self.conditions:
            conditions_count += 1
            # Filter out the standard conditions
            if c.condition_id not in (1001, 1002, 1004):
                conditions.append(str(c))
        conditions_body = None
        if conditions_count == 0:
            conditions_body = 'We have not imported any conditions for this battle.'
        elif conditions_count == 3:
            conditions_body = 'There are no specific conditions for this battle.'
        self._main_panels.append(
            {
                'title': 'Specific Conditions',
                'body': conditions_body,
                'items': conditions,
                'footer': 'You may lose a max of {} medals and still achieve champion for this battle.'.format(conditions_count//2) if conditions_count else '',
            }
        )

        enemies = []
        for enemy in sorted(self.enemies, key=lambda x: x.is_sp_enemy):
            item = '<a href="/{}">{}</a>'.format(enemy.search_id, enemy)
            if enemy.is_sp_enemy:
                item = '<strong>{}</strong>'.format(item)
            enemies.append(item)
        self._main_panels.append(
            {
                'title': 'Enemies',
                'body': '' if self.enemies else 'No items found in database.',
                'items': enemies,
                'footer': 'These items are not all inclusive.<br>Bold name indicates a boss.'
            }
        )

        drops = []
        for drop in sorted(self.drops, key=lambda x: x.drop_id):
            if drop.drop_id > 90000000:
                # Filter out 'COMMON' drops
                continue
            item = '<a href="/{}">{} from {}</a>'.format(
                    drop.drop_id, drop.drop.name, drop.enemy)
            if drop.enemy.is_sp_enemy:
                item = '<strong>{}</strong>'.format(item)
            drops.append(item)
        self._main_panels.append(
            {
                'title': 'Drops',
                'body': '' if self.drops else 'No items found in database.',
                'items': drops,
                'footer': 'Bold indicates a boss.<br>*To be improved (maybe).',
            }
        )

    def __init__(self, **kwargs):
        for i in (
            'order_no',
            'rank',
            'is_unlocked',
        ):
            if i in kwargs:
                del(kwargs[i])

        super(Battle, self).__init__(**kwargs)

    def __repr__(self):
        return '{}>{}'.format(self.dungeon, self.name)


ATTRIBUTE_ID = {
    # Elements
    100: 'Fire',
    101: 'Ice',
    102: 'Lightning',
    103: 'Earth',
    104: 'Wind',
    105: 'Water',
    106: 'Holy',
    107: 'Dark',
    108: 'Poison (Bio)',

    # Status
    200: 'Poison (Status)',
    201: 'Silence',
    202: 'Paralysis',
    203: 'Confuse',
    204: 'Haste',
    205: 'Slow',
    206: 'Stop',
    207: 'Protect',
    208: 'Shell',
    209: 'Reflect',
    210: 'Blind',
    211: 'Sleep',
    212: 'Petrify',
    213: 'Doom',
    214: 'Death',
    215: 'Berserk',
    216: 'Regen',
    217: 'Reraise',
    218: 'Float',
    219: 'Weak',
    220: 'Zombie',
    221: 'Mini',
    222: 'Toad',
    223: 'Curse',
    224: 'Slownumb',
    225: 'Blink',
    #226: 'Water Imp',
    #227: 'Vanish',
    #228: 'Porky',
    #229: 'Sap',
}

FACTOR = {
    21: 'Absorb',
    11: 'Null',
    6: 'Resist',
    1: 'Weak',
}

FACTOR_STATUS = {
    1: 'Immune',
    0: 'Vulnerable',
}

def get_factor(attribute_id, factor):
    if attribute_id < 200:
        return FACTOR.get(factor)
    return FACTOR_STATUS.get(factor)

class AttributeAssociation(BetterBase):
    __tablename__ = 'attribute_table'
    attribute_id = Column(Integer, ForeignKey('attribute.id'), primary_key=True)
    param_id = Column(Integer, primary_key=True, autoincrement=False)
    # Not a ForeignKey('enemy.param_id') because enemy.param_id is not unique

    attribute = relationship('Attribute')

    def __init__(self, **kwargs):
        super(AttributeAssociation, self).__init__(**kwargs)

    def __repr__(self):
        return '{}'.format(self.attribute)

class Attribute(BetterBase):
    __tablename__ = 'attribute'
    id = Column(Integer, primary_key=True, autoincrement=True)
    attribute_id = Column(TINYINT(unsigned=True), nullable=False)
    factor = Column(TINYINT, nullable=False)
    #name = Column(String(length=16))

    def __init__(self, **kwargs):
        super(Attribute, self).__init__(**kwargs)
        #self.name = ATTRIBUTE_ID.get(self.attribute_id, '')

    def __repr__(self):
        #return '{}: {}'.format(
        #    self.name, get_factor(self.attribute_id, self.factor))
        return '{}: {}'.format(
            ATTRIBUTE_ID.get(self.attribute_id, self.attribute_id),
            get_factor(self.attribute_id, self.factor)
        )

# 2015-05-27
# Maybe deprecated depending on status of Attribute.name
def populate_attribute_names():
    '''
    Get Attribute() objects with no name and attempts to populate the name.
    This might run with cron although the name are hardcoded.
    '''
    with session_scope() as session:
        attributes = session.query(Attribute).filter(Attribute.name == '').all()
        for attribute in attributes:
            attribute.name = ATTRIBUTE_ID.get(attribute.attribute_id, '')
            if not attribute.name:
                logging.warning(
                    'Attribute({}) still has no name.'.format(attribute))


class Enemy(BetterBase):
    __tablename__ = 'enemy'
    # id is our database unique primary_key (for different stats/levels)
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Vargas and Ipooh have the same enemy_id
    enemy_id = Column(Integer, nullable=False)
    # param_id is the unique id per enemy
    # Dullahan has multiple param_ids for the different resistances
    param_id = Column(Integer, nullable=False)
    name = Column(String(length=32), nullable=False)
    # There are at least two different Enemy.filter(Enemy.name == 'Behemoth')
    # And unlike Flan there is not a Realm identifier in the name
    breed_id = Column(TINYINT, nullable=False)
    size = Column(TINYINT, nullable=False)
    is_sp_enemy = Column(TINYINT, nullable=False)
    event_id = Column(SMALLINT, nullable=True)
    event_type = Column(String(length=16), nullable=True)

    lv = Column(TINYINT, nullable=False)
    max_hp = Column(Integer, nullable=False)
    acc = Column(SMALLINT, nullable=False)
    atk = Column(SMALLINT, nullable=False)
    critical = Column(SMALLINT, nullable=False)
    defense = Column(SMALLINT, nullable=False)
    eva = Column(SMALLINT, nullable=False)
    looking = Column(Integer, nullable=False)
    matk = Column(SMALLINT, nullable=False)
    mdef = Column(SMALLINT, nullable=False)
    mnd = Column(SMALLINT, nullable=False)
    spd = Column(SMALLINT, nullable=False)

    #counters = relationship('counters')
    exp = Column(SMALLINT, nullable=False)

    frontend_columns = (
        ('name', 'Name'),
        ('is_sp_enemy', 'Boss'),
        ('event_id', 'Event ID'),
    )

    @property
    def search_id(self):
        # enemy_id 4xxxxx may have the same id as the elite dungeon it is in
        # So we have to query by param_id or use get_by_id(enemy=True)
        #return self.enemy_id
        return self.param_id

    def get_attributes(self):
        aas = []
        with session_scope() as session:
            aas = session.query(AttributeAssociation)\
                        .filter(AttributeAssociation.param_id == self.param_id)\
                        .options(subqueryload(AttributeAssociation.attribute))\
                        .all()
            session.expunge_all()
        return aas

    def generate_main_panels(self):
        self._main_panels = [
            {
                'title': 'Main Stats',
                'items': [
                    'Name: {}'.format(self.name),
                ],
            },
        ]

        # get_by_id() does not work here because we need the group_by
        params = []
        with session_scope() as session:
            q = session.query(Enemy)\
                       .filter(Enemy.enemy_id == self.enemy_id)\
                       .group_by('param_id')
            params = q.all()
            session.expunge_all()

        for param in params:
            aas = param.get_attributes()
            self._main_panels.append(
                {
                    'title': 'Resistances',
                    'body': param.name,  # picture probably
                    'items': sorted(
                        aas,
                        key=lambda x: x.attribute.attribute_id
                    ),
                    'footer': '*To be improved (maybe).',
                }
            )

        self._main_panels += (
            {
                'title': 'Abilities',
                'footer': '*To be implemented (hopefully).',
            },
            {
                'title': 'Battle Locations',
                'footer': '*To be implemented (maybe).',
            },
            {
                'title': 'Drops',
                'footer': '*To be implemented (maybe).',
            },
        )
        if self.is_sp_enemy:
            self._main_panels[0]['items'].append('BOSS')

    @property
    def extra_tabs(self):
        return (
            {
                'id': 'stats',
                'title': 'Stats by Level',
                'search_id': self.enemy_id,
                'extra_params': '&enemy=1',
                'columns': (
                    ('name', 'Name'),
                    ('lv', 'Level'),
                    ('max_hp', 'Max HP'),
                    ('atk', 'ATK'),
                    ('acc', 'ACC'),
                    ('critical', 'Critical'),
                    ('defense', 'DEF'),
                    ('eva', 'EVA'),
                    ('matk', 'MAG'),
                    ('mdef', 'RES'),
                    ('mnd', 'MIND'),
                    ('spd', 'SPD'),
                    ('exp', 'EXP'),
                ),
            },
        )

    def __init__(self, **kwargs):
        for k, v in kwargs['params'].items():
            kwargs[k] = v
        kwargs['defense'] = kwargs['def']
        kwargs['name'] = kwargs['disp_name']
        kwargs['param_id'] = kwargs['params']['id']
        for i in (
            'id',
            'ai_id',
            'child_pos_id',
            'init_hp',
            'no',
            'params',
            'def',
            'disp_name',
            'counters',
            'def_attributes',
            'animation_info',
            'uid',
            'deform_animation_info',
            'drop_item_list',
            'abilities',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Enemy, self).__init__(**kwargs)

    def __repr__(self):
        return '{} ({})'.format(self.name, self.lv)


class AbilityCost(BetterBase):
    __tablename__ = 'abilitycost'
    ability_id = Column(Integer, ForeignKey('ability.id'), primary_key=True)
    material_id = Column(Integer, ForeignKey('material.id'), primary_key=True)
    count = Column(TINYINT, nullable=False)

    material = relationship('Material',
                            backref=backref('abilities', lazy='select'),
                            #backref=backref('abilities', lazy='immediate'),
                            #backref=backref('abilities', lazy='joined'),
                            #backref=backref('abilities', lazy='subquery'),
                            #backref=backref('abilities', lazy='noload'),
                            #backref=backref('abilities', lazy='dynamic'),
                            #order_by='Ability.id',
    )
    ability = relationship('Ability',
                           backref=backref('materials', lazy='select'),
                           #backref=backref('materials', lazy='immediate'),
                           #backref=backref('materials', lazy='joined'),
                           #backref=backref('materials', lazy='subquery'),
                           #backref=backref('materials', lazy='noload'),
                           #backref=backref('materials', lazy='dynamic'),
    )

    def __init__(self, **kwargs):
        super(AbilityCost, self).__init__(**kwargs)

    def __repr__(self):
        return '{} {}'.format(self.count, self.material)


class Ability(BetterBase):
    __tablename__ = 'ability'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ability_id = Column(Integer, nullable=False)
    name = Column(String(length=32), nullable=False)
    description = Column(String(length=256), nullable=False)

    rarity = Column(TINYINT, nullable=False)
    category_id = Column(TINYINT, nullable=False)
    category_name = Column(String(length=32), nullable=False)
                  # ('Spellblade', 'Celerity', 'Combat', etc.)
    category_type = Column(TINYINT, nullable=False)
                  # {1:Black, 2:White, 3:Physical, 4:Summon, 5:Other}
    target_range = Column(TINYINT, nullable=False)
                  # {1:Single, 2:AOE?}

    grade = Column(TINYINT, nullable=False)
    next_grade = Column(TINYINT, nullable=False)
    max_grade = Column(TINYINT, nullable=False)
    arg1 = Column(TINYINT, nullable=False)  # Number of casts
    #arg2 = Column(TINYINT, nullable=False)  # Unknown (all are zero)
    #arg3 = Column(TINYINT, nullable=False)  # Unknown (all are zero)
    required_gil = Column(Integer, nullable=False)
    sale_gil = Column(SMALLINT, nullable=False)

    frontend_columns = (
        ('name', 'Name'),
        ('rarity', 'Rarity'),
        ('category_name', 'Category'),
        ('category_type', 'Category Type'),
    )

    main_columns = frontend_columns + (('grade', 'Grade'), ('arg1', 'Casts'),)

    def generate_main_panels(self):
        main_stats = []
        for k, v in self.frontend_columns:
            main_stats.append('{}: {}'.format(v, self.__getattribute__(k)))
        main_stats.append('Target Range: {}'.format(self.target_range))

        self._main_panels = [
            {
                'title': 'Main Stats',
                'body': self.description if self.description else '',
                'items': main_stats,
            },
        ]

        with session_scope() as session:
            # The self.materials backref does not help here
            # because they are only applicable to this self.id
            # and not to the self.ability_id
            grades = session.query(Ability).filter_by(
                ability_id=self.ability_id).order_by(
                    'grade').all()
            for grade in grades:
                grade_panel = {'title': 'Grade {}'.format(grade.grade)}
                gil = grade.required_gil
                if gil is None or gil == 32767:
                    gil = 'Unknown'
                grade_panel['items'] = [
                    'Casts: {}'.format(grade.arg1),
                    'Creation/Enhancement cost: {}'.format(gil),
                    'Sale gil: {}'.format(grade.sale_gil),
                ]
                for cost in grade.materials:
                    grade_panel['items'].append(
                        '<a href="/{}">{}: {} Orbs</a>'.format(
                            cost.material.search_id, cost.material, cost.count)
                    )
                self._main_panels.append(grade_panel)

        self._main_panels.append(
            {
                'title': 'Total required',
                'footer': '*To be implemented (maybe).',
            }
        )

    @property
    def search_id(self):
        return self.ability_id

    def __init__(self, **kwargs):
        if kwargs['arg2'] or kwargs['arg3']:
            logging.critical(
                'Ability {} has additional args'.format(kwargs['name']))
        for i in (
            'arg2',  # all zero
            'arg3',  # all zero
            'factor_category',  # all one
            'command_icon_path',
            'image_path',
            'thumbnail_path',
            'material_id_2_num',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Ability, self).__init__(**kwargs)

    def __repr__(self):
        return '[{}*] {} {}/{}'.format(
            self.rarity, self.name, self.grade, self.max_grade)


'''
class EnemyAbility(BetterBase):
    __tablename__ = 'enemy_ability'
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(length=32))

    def __init__(self, **kwargs):
        super(EnemyAbility, self).__init__(**kwargs)

    def __repr__(self):
        return self.name
'''


class Drop(BetterBase):
    __tablename__ = 'drop'
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(length=32), default='')

    def __repr__(self):
        if self.name:
            return self.name
        return str(self.id)

    def populate_name(self):
        if self.name is not None:
            return

        name = get_name_by_id(self.id)
        if name != self.id:
            self.name = name
            new_log = Log(log='Add name to Drop({})'.format(self))
            with session_scope() as session:
                session.add(new_log)

def populate_drop_names():
    '''
    Get Drop() objects with no name and attempts to populate the name.
    This might run with cron.
    '''
    with session_scope() as session:
        drops = session.query(Drop).filter(Drop.name == '').all()
        for drop in drops:
            drop.populate_name()
            if not drop.name:
                logging.warning('Drop({}) still has no name.'.format(drop))


class Material(BetterBase):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(length=64), nullable=False)
    rarity = Column(TINYINT, nullable=False)
    sale_gil = Column(SMALLINT, nullable=False)
    description = Column(String(length=256), nullable=False)

    frontend_columns = (
        ('name', 'Name'),
        ('rarity', 'Rarity'),
        ('sale_gil', 'Sale gil'),
        #('description', 'Description'),
    )

    main_columns = frontend_columns

    @property
    def search_id(self):
        return self.id

    '''
    # There is only one item with self.search_id
    @property
    def extra_tabs(self):
        return (
            {
                'id': 'stats',
                'title': 'Stats by Rarity',
                'columns': self.main_columns,
                'search_id': self.search_id,
            },
        )
    '''

    def generate_main_panels(self):
        main_stats = []
        for k, v in self.main_columns:
            main_stats.append('{}: {}'.format(v, self.__getattribute__(k)))

        crafting_recipes = []
        for cost in sorted(self.abilities,
                        key=lambda x: x.ability.ability_id + x.ability.grade):
            # It would be cool to make each ability item expand to show the
            # cost per grade on the frontend.
            crafting_recipes.append(
                '<a href="/{}">{}: {} Orbs</a>'.format(
                    cost.ability.search_id, cost.ability, cost.count)
            )

        # This is repeated in Relic.main_panels
        # This queries drop_table, enemy, world, dungeon, battle
        # TODO 2015-05-11
        # Filter out (expired?) events
        drop_locations = []
        with session_scope() as session:
            drops = session.query(DropAssociation).filter_by(
                drop_id=self.search_id).options(subqueryload('enemy')).all()
            for drop in drops:
                drop_locations.append(
                    '<a href="/{}">{}</a>'.format(
                        drop.enemy.search_id, str(drop)))

        self._main_panels = (
            {
                'title': 'Main Stats',
                'body': self.description if self.description else '',
                'items': main_stats,
            },
            {
                'title': 'Abilities',
                'items': crafting_recipes,
                'footer': '*To be improved.',
            },
            {
                'title': 'Drop Locations',
                'items': drop_locations,
                'footer': 'These locations are not all inclusive and the drop rates may vary.',
            },
        )

    def __init__(self, **kwargs):
        for i in ('image_path', 'created_at', 'num'):
            if i in kwargs:
                del(kwargs[i])
        super(Material, self).__init__(**kwargs)

    def __repr__(self):
        return '{}'.format(self.name)


class Relic(BetterBase):
    __tablename__ = 'relic'
    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer)
    name = Column(String(length=64), nullable=False)
    base_rarity = Column(TINYINT, nullable=False)
    rarity = Column(TINYINT, nullable=False)
    level = Column(TINYINT, nullable=False)
    level_max = Column(TINYINT, nullable=False)
    evolution_num = Column(TINYINT, nullable=False)
    max_evolution_num = Column(TINYINT, nullable=False)
    can_evolve_potentially = Column(Boolean, nullable=False)
    is_max_evolution_num = Column(Boolean, nullable=False)
    series_id = Column(Integer, nullable=False)

    description = Column(String(length=256), nullable=False)
    has_someones_soul_strike = Column(Boolean, nullable=False)
    has_soul_strike = Column(Boolean, nullable=False)
    soul_strike_id = Column(Integer)
    required_enhancement_base_gil = Column(SMALLINT)
    required_evolution_gil = Column(Integer)
    sale_gil = Column(SMALLINT, nullable=False)

    acc = Column(SMALLINT, nullable=False)
    atk = Column(SMALLINT, nullable=False)
    critical = Column(SMALLINT, nullable=False)
    defense = Column(SMALLINT, nullable=False)
    eva = Column(SMALLINT, nullable=False)
    matk = Column(SMALLINT, nullable=False)
    mdef = Column(SMALLINT, nullable=False)
    mnd = Column(SMALLINT, nullable=False)
    series_acc = Column(SMALLINT, nullable=False)
    series_atk = Column(SMALLINT, nullable=False)
    series_def = Column(SMALLINT, nullable=False)
    series_eva = Column(SMALLINT, nullable=False)
    series_matk = Column(SMALLINT, nullable=False)
    series_mdef = Column(SMALLINT, nullable=False)
    series_mnd = Column(SMALLINT, nullable=False)

    category_id = Column(TINYINT, nullable=False)
    category_name = Column(String(length=32), nullable=False)
    equipment_type = Column(TINYINT, nullable=False)    # 1:"Weapon", 2:"Armor", 3:"Accessory"
    # "allowed_buddy_id": 0,                            # This might be for specific characters only
    # "atk_ss_point_factor": 0,                         # I guess this increases the soul strike charge rate?
    # "def_ss_point_factor": 0,                         # I guess this increases the soul strike charge rate?
    # "attributes": [],                                 # What?
    # "can_evolve_now": false,                          # Don't care?
    # "created_at": 1428491598,                         # Don't care
    # "exp": 0,                                         # This is the exp for this Relic instance
    # "id": 49594264,                                   # This is the id for this Relic instance
    # "is_sp_enhancement_material": false,              # Don't care
    # "is_usable_as_enhancement_material": false,       # Don't care
    # "is_usable_as_enhancement_src": false,            # Don't care
    # "evol_max_level_of_base_rarity": {}               # Don't care

    frontend_columns = (
        ('name', 'Name'),
        ('base_rarity', 'Rarity'),
        ('category_name', 'Category'),
        #('equipment_type', 'Type'),
    )

    @property
    def search_id(self):
        return self.equipment_id

    @property
    def extra_tabs(self):
        return (
            {
                'id': 'stats',
                'title': 'Stats by Level',
                'search_id': self.search_id,
                'columns': (
                    ('rarity', 'Rarity'),
                    ('level', 'Level'),
                    ('required_enhancement_base_gil', 'Enhancement cost'),
                    ('required_evolution_gil', 'Evolution cost'),
                    ('sale_gil', 'Sale gil'),
                    ('atk', 'ATK'),
                    ('critical', 'CRIT'),
                    ('defense', 'DEF'),
                    ('acc', 'ACC'),
                    ('eva', 'EVA'),
                    ('matk', 'MAG'),
                    ('mdef', 'RES'),
                    ('mnd', 'MIND'),
                    ('series_acc', 'RS ACC'),
                    ('series_atk', 'RS ATK'),
                    ('series_def', 'RS DEF'),
                    ('series_eva', 'RS EVA'),
                    ('series_matk', 'RS MAG'),
                    ('series_mdef', 'RS RES'),
                    ('series_mnd', 'RS MIND'),
                ),
            },
        )

    def generate_main_panels(self):
        main_stats = []
        for k, v in self.main_columns:
            main_stats.append('{}: {}'.format(v, self.__getattribute__(k)))
        if self.has_soul_strike:
            main_stats.append('Soul Strike: {} [TO BE IMPLEMENTED]'.format(
                self.soul_strike_id))

        # This is repeated in Material.main_panels
        # This queries drop_table, enemy, world, dungeon, battle
        # TODO 2015-05-11
        # Filter out (expired?) events
        drop_locations = []
        with session_scope() as session:
            drops = session.query(DropAssociation).filter_by(
                drop_id=self.search_id).options(subqueryload('enemy')).all()
            for drop in drops:
                drop_locations.append(
                    '<a href="/{}">{}</a>'.format(
                        drop.enemy.search_id, str(drop)))

        self._main_panels = (
            {
                'title': 'Main Stats',
                'body': self.description if self.description != 'None' else '',
                'items': main_stats,
            },
            {
                'title': 'Drop Locations',
                'items': drop_locations,
                'footer': 'These locations are not all inclusive and the drop rates may vary.',
            },
        )

    def __init__(self, **kwargs):
        name = kwargs['name']
        name = name.replace(u'\uff0b', '')
        name = name.encode(sys.stdout.encoding, errors='ignore')
        kwargs['name'] = name
        kwargs['defense'] = kwargs['def']

        for i in (
            "allowed_buddy_id",
            "atk_ss_point_factor",
            "def_ss_point_factor",
            "attributes",
            "can_evolve_now",
            "created_at",
            "exp",
            "is_sp_enhancement_material",
            "is_usable_as_enhancement_material",
            "is_usable_as_enhancement_src",
            "evol_max_level_of_base_rarity",
            "detail_image_path",
            "image_path",
            "thumbnail_path",
            "def",
            "id",
        ):
            if i in kwargs:
                del(kwargs[i])

        super(Relic, self).__init__(**kwargs)

    def __repr__(self):
        ret = '[{}*] {}'.format(self.rarity, self.name)
        if self.evolution_num:
            ret += ' ' + '+'*self.evolution_num
        ret += ' {}/{}'.format(self.level, self.level_max)
        return ret


class DropAssociation(BetterBase):
    __tablename__ = 'drop_table'
    enemy_id = Column(Integer, ForeignKey('enemy.id'), primary_key=True)
    drop_id = Column(Integer, ForeignKey('drop.id'), primary_key=True)
    battle_id = Column(Integer, ForeignKey('battle.id'), primary_key=True)

    enemy = relationship('Enemy',
                         backref=backref('drops'),
    )
    drop = relationship('Drop',
                        backref=backref('drop_associations'),
    )
    battle = relationship('Battle',
                          backref=backref('drops'),
    )

    def __init__(self, **kwargs):
        super(DropAssociation, self).__init__(**kwargs)

    def __repr__(self):
        return '{} from {} in {}'.format(self.drop, self.enemy, self.battle)

def check_exists(equipment_id, level, rarity):
    with session_scope() as session:
        q = session.query(Relic).filter_by(equipment_id=equipment_id,
                                           level=level, rarity=rarity)
        r = session.query(q.exists()).scalar()
    return r

def get_load_data(data, filepath):
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)
    return data

def import_dammitdame(filepath):
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    with session_scope() as session:
        pass
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))

def import_equipmentbuilder(filepath):
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    with session_scope() as session:
        pass
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))

def import_battle_list(data=None, filepath=''):
    '''
    /dff/world/battles
    '''
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

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
    '''
    /dff/world/dungeons
    '''
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
            prizes = dungeon['prizes']
            new_dungeon = session.query(Dungeon).filter_by(
                id=dungeon['id']).first()
            if new_dungeon is None:
                new_dungeon = Dungeon(**dungeon)
                session.add(new_dungeon)
                session.commit()
                new_log = Log(log='Create Dungeon({})'.format(new_dungeon))
                session.add(new_log)
            for prize_type, prizes_list in prizes.items():
                for prize in prizes_list:
                    id = prize['id']
                    name = prize['name']
                    drop = session.query(Drop).filter_by(
                        id=id).first()
                    if drop is None:
                        drop = Drop(id=id, name=name)
                        # Is this automatically added to the session?
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
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success

def import_win_battle(data=None, filepath=''):
    '''
    /dff/battle/win
    /dff/event/wday/9/win_battle
    '''
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
            # How the hell would this happen?
            return False

        score = data['result']['score']
        general = score['general']
        specific = score['specific']
        for s in general + specific:
            # Get the condition if it already exists
            old_condition = session.query(Condition).filter_by(
                title=s['title'], condition_id=s['id'], code_name=s['code_name']
            ).first()
            if old_condition is None:
                # Make a new condition if it does not exist yet
                old_condition = Condition(**s)
                session.add(old_condition)
                session.commit()
                new_log = Log(
                    log='Create Condition({})'.format(old_condition))
                session.add(new_log)
            if old_condition not in battle.conditions:
                battle.conditions.append(old_condition)
                new_log = Log(log='Add Condition({}) to Battle({})'.format(
                    old_condition, battle))
                session.add(new_log)
                session.commit()
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success

def import_battle(data=None, filepath=''):
    '''
    get_battle_init_data
    '''
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

    success = False
    with session_scope() as session:
        battle = data['battle']
        battle_id = battle['battle_id']
        for round in battle['rounds']:
            for enemy in round['enemy']:
                for e in enemy['children']:
                    new_drops = []
                    for drop in e['drop_item_list']:
                        # Get/Create Enemy()
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
                                log='Create Enemy({})'.format(new_enemy))
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
                                # Ugh, this outpus None for the association
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
                                'We are missing a battle object for {}'\
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
                                log='Add Enemy({}) to Battle({})'.format(
                                    new_enemy, old_battle))
                            session.add(new_log)
                        session.commit()
                        # TODO 2015-05-10
                        # Improve this nesting indentation
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success

def import_party(data=None, filepath=''):
    '''
    /dff/party/list
    '''
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

    success = False
    with session_scope() as session:
        equipments = data['equipments']
        for e in equipments:
            if check_exists(e.get('equipment_id'),
                            e.get('level'), e.get('rarity')):
                continue
            new_relic = Relic(**e)
            new_log = Log(log='Create Relic({})'.format(new_relic))
            session.add_all((new_relic, new_log))
            session.commit()

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
            # Check if the Character() exists
            old_character = session.query(Character).filter(
                Character.buddy_id == c['buddy_id'],
                Character.level == c['level']).first()
            if old_character is not None:
                for i, ec in c['equipment_category'].items():
                    ce = session.query(CharacterEquip).filter(
                        CharacterEquip.category_id == ec['category_id'],
                        CharacterEquip.equipment_type == ec['equipment_type'],
                        CharacterEquip.buddy_id == old_character.buddy_id)\
                                                      .first()
                    if ce is not None:
                        continue
                    ec['buddy_id'] = old_character.buddy_id
                    ce = CharacterEquip(**ec)
                    new_log = Log(
                        log='Add {}({}) to {}({})'.format(
                            type(ce).__name__, ce,
                            type(old_character).__name__, old_character))
                    session.add_all((ce, new_log))
                for i, ac in c['ability_category'].items():
                    ca = session.query(CharacterAbility).filter(
                        CharacterAbility.category_id == ac['category_id'],
                        CharacterAbility.buddy_id == old_character.buddy_id)\
                                                        .first()
                    if ca is not None:
                        continue
                    ac['buddy_id'] = old_character.buddy_id
                    ca = CharacterAbility(**ac)
                    new_log = Log(
                        log='Add {}({}) to {}({})'.format(
                            type(ca).__name__, ca,
                            type(old_character).__name__, old_character))
                    session.add_all((ca, new_log))
                session.commit()
                continue
            new_character = Character(**c)
            new_log = Log(log='Create {}({})'.format(
                type(new_character).__name__, new_character))
            session.add_all((new_character, new_log))
            session.commit()
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success

def import_dff(data=None, filepath=''):
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

    # This is the series we are currently in
    #series_id = data.get('dungeon_session', {})\
    #                .get('party_status', {}).get('series_id', -1)
    # Which we do not need

    # This is a dict representing our current party
    party = data.get('party', {}).get('slot_to_buddy_id', {})
    success = False
    with session_scope() as session:
        equipments = data['equipment']
        for c in data.get('buddy', ()):
            old_character = session.query(Character).filter(
                Character.buddy_id == c['buddy_id'],
                Character.level == c['level']).first()
            if old_character is not None:
                continue
            okay = True
            # Check if the Character() is not in our party
            #if c['id'] not in party.values():
            #    continue
            # If we are doing import_party on dff we have to do equipments
            for e_id in ('accessory_id', 'armor_id', 'weapon_id'):
                e_id = c.get(e_id)
                # Skip if we do not have anything equipped
                if e_id == 0:
                    continue
                # Get the equipment
                for equipment in equipments:
                    if equipment.get('id') == e_id:
                        break
                if equipment.get('id') != e_id:
                    logging.critical(
                        'Equipment with id={} not found.'.format(e_id))
                    logging.critical('Skipping this import.')
                    okay = False
                    break
                keys = ('acc', 'atk', 'def', 'eva', 'matk', 'mdef', 'mnd')
                # no 'hp', 'spd' as of 2015-06-03
                # Remove the stats from both the Character() base and series
                for k in keys:
                    c[k] -= equipment[k]
                    # Check if we are in the series
                    if equipment['series_id'] == c['series_id']:
                        c['series_{}'.format(k)]\
                            -= equipment['series_{}'.format(k)]
                    else:
                        c['series_{}'.format(k)] -= equipment[k]
            if okay:
                new_character = Character(**c)
                new_log = Log(log='Create {}({})'.format(
                    type(new_character).__name__, new_character))
                session.add_all((new_character, new_log))
                session.commit()
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success

def import_recipes(data=None, filepath=''):
    '''
    /dff/ability/get_generation_recipes
    /dff/ability/get_upgrade_recipes
    '''
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

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

def import_ability_upgrade(data=None, filepath=''):
    '''
    /dff/ability/upgrade
    '''
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

    success = False
    with session_scope() as session:
        a = data['upgraded_ability']
        old_ability = session.query(Ability).filter_by(
            ability_id=a['ability_id'], grade=a['grade']).first()
        if old_ability is None:
            logging.error('How are we upgrading an ability that we do not have in our database?')
        elif old_ability.required_gil == 32767 and\
        old_ability.required_gil < a['required_gil']:
            old_ability.required_gil = a['required_gil']
            new_log = Log(log='Update Ability({}).required_gil'.format(
                old_ability)
            )
            session.add(new_log)
            session.commit()
        success = True
    return success

def import_enhance_evolve(data=None, filepath=''):
    '''
    /dff/equipment/enhance
    /dff/equipment/evolve
    '''
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

    success = False
    with session_scope() as session:
        for e in (data['old_src_user_equipment'],
                  data['new_src_user_equipment'],):
            if check_exists(e.get('equipment_id'),
                            e.get('level'), e.get('rarity')):
                continue
            new_relic = Relic(**e)
            new_log = Log(log='Create Relic({})'.format(new_relic))
            session.add_all((new_relic, new_log))
            session.commit()
        success = True
    return success

def import_grow(data=None, filepath=''):
    '''
    /dff/grow_egg/use
    '''
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

    c = data['buddy']

    success = False
    with session_scope() as session:
        if not session.query(session.query(Character).filter(
                Character.buddy_id == c['buddy_id'],
                Character.level == c['level']).exists()).scalar():
            new_character = Character(**c)
            new_log = Log(log='Create {}({})'.format(
                type(new_character).__name__, new_character))
            session.add_all((new_character, new_log))
            session.commit()
        success = True
    return success


# Commented out because recordpeeker.handle_party_list() is superior.
'''
WEAPON_CATEGORIES = (
    'Axe',
    'Ball',
    'Book',
    'Bow',
    'Dagger',
    'Fist',
    'Hammer',
    'Instrument',
    'Katana',
    'Rod',
    'Spear',
    'Staff',
    'Sword',
    'Thrown',
    'Whip',
)

def rank_relics(order_by='atk', equipment_type=WEAPON,
                categories=WEAPON_CATEGORIES, realm=None, count=1):
    if isinstance(realm, int) and realm < 100001:
        realm = 100001 + int(realm) * 1000
    outlist = {}
    with session_scope() as session:
        base_query = session.query(Relic)
        ordered_queries = [base_query.order_by(desc(order_by))]
        if realm is not None:
            ordered_queries.append(base_query.order_by(
                desc('series_' + order_by)).filter_by(series_id=realm))
        for c in categories:
            for o in ordered_queries:
                subquery = o.filter_by(category_name=c).subquery()
                results = session.query().add_entity(
                    Relic, alias=subquery).group_by(
                        'equipment_id').limit(count).all()
                for r in results:
                    if c not in outlist:
                        outlist[c] = [r]
                        continue
                    outlist[c].append(r)
        session.expunge_all()
    return outlist
'''

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
            (Enemy, Enemy.param_id, ('lv', )),
            (Character, Character.buddy_id, ('level', )),
        ):
            q = session.query(m)
            q = q.filter(c == id)
            for i in o:
                q = q.order_by(i)
            # joinedload('*') is slow
            #q = q.options(joinedload('*'))
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
