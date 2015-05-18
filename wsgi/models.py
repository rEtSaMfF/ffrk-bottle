#!/usr/bin/env python2

import decimal
import os
import sys
import json
import logging
import time
import traceback

from sqlalchemy import create_engine, Column, Integer, String, Boolean,\
    ForeignKey, Table, desc, event
from sqlalchemy.engine import Engine
from sqlalchemy.types import TIMESTAMP, DateTime
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT
from sqlalchemy.ext.declarative import declarative_base as real_declarative_base
from sqlalchemy.orm import sessionmaker, load_only, relationship, backref,\
    joinedload, subqueryload, lazyload

from contextlib import contextmanager
from datetime import datetime
from humanize import naturalday, naturaltime


# TODO 2015-05-11
# Change all DateTime columns to TIMESTAMP


### SQLALCHEMY INIT START ###
# Make this a class decorator
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
    def column_items(self):
        return dict(((c, getattr(self, c)) for c in self.columns))

    @property
    def frontend_columns(self):
        '''
        The columns we see when listing all objects of this class.
        '''
        return ((c,c) for c in self.columns)

    @property
    def main_columns(self):
        '''
        The columns we see when listing similar objects of this class.
        Example: listing the stats per level.
        '''
        return self.frontend_columns

    @property
    def search_id(self):
        '''
        The id used to search for this object ignoring varying attributes such
        as stats per level.
        '''
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
    # Will be an iterable of dicts representing objects similar to this object
    # such as stats per level.

    def __repr__(self):
        return u'{}({})'.format(self.__class__.__name__, self.column_items)

    def tojson(self):
        return self.column_items

    def dict(self):
        '''
        Transform the model into a dictionary.
        '''
        # first we get the names of all the columns on your model
        #columns = (c.key for c in class_mapper(self.__class__).columns)
        # then we return their values in a dict
        #return dict((c, getattr(self, c)) for c in columns)
        ret = dict((c, getattr(self, c)) for c in self.column_items)
        if self.search_id is not None:
            ret['search_id'] = self.search_id
        return ret

    def jsonify(self):
        '''
        Transform the model into JSON.
        '''
        return json.dumps(self.dict(), default=default_encode)

def default_encode(obj):
    if isinstance(obj, decimal.Decimal):
        return u'{:.2f}'.format(self._value)
    if isinstance(obj, datetime):
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()

        obj = obj.replace(tzinfo=None)
        return (obj - datetime(1970,1,1)).total_seconds()
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
        print (e, e.args)
        print (traceback.print_exc())
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
### SQLALCHEMY INIT END ###


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

ARMOR_CATEGORIES = (
    'Armor',
    'Bracer',
    'Hat',
    'Helm',
    'Light Armor',
    'Robe',
    'Shield',
)

WEAPON = 1
ARMOR = 2
ACCESSORY = 3

def make_tables():
    BetterBase.metadata.create_all(engine)

enemy_table = Table('enemy_table', BetterBase.metadata,
                    Column('enemy_id', Integer, ForeignKey('enemy.id'),
                           nullable=False),
                    Column('battle_id', Integer, ForeignKey('battle.id'),
                           nullable=False),
)


# Should this be BetterBase?
class About(object):
    name = 'About'

    main_panels = (
        {
            'title': 'About',
            'body': 'A FINAL FANTASY Record Keeper Database',
            #'items': ('items{}'.format(i) for i in range(5)),
            'footer': '*Work in progress',
        },
    )


'''
# I do not want to import these because the stats include equipment
# But then again we may subtract those stats....
class Character(BetterBase):
    __tablename__ = 'character'
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(length=32), nullable=False)
    job_name = Column(String(length=32), nullable=False)
    description = Column(String(length=256), nullable=False)
    series_id = Column(Integer, nullable=False)

    level = Column(TINYINT, nullable=False)
    level_max = Column(TINYINT, nullable=False)

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

    #ability_category = 
    #equipment_category = 

    def __init__(self, **kwargs):
        kwargs['id'] = kwargs['buddy_id']
        kwargs['defense'] = kwargs['def']
        kwargs['description'] = kwargs['description'].encode(sys.stdout.encoding, errors='ignore')
        for i in (
            'ability_1_id',
            'ability_2_id',
            'accessory_id',
            'weapon_id',
            'armor_id',
            'buddy_id',
            'created_at',
            'def',
            'exp',
            'row',
            'soul_strike_id',
            'image_path',

            'default_soul_strike_id',
            'ability_category',
            'equipment_category',
        ):
            if i in kwargs:
                del(kwargs[i])
'''


class Log(BetterBase):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    log = Column(String(length=256), nullable=False)
    # I want a way to reference the objects in this log but that is not too easy

    frontend_columns = (
        ('timestamp', 'Timestamp'),
        ('log', 'Log'),
    )

    search_id = None

    def __init__(self, **kwargs):
        super(Log, self).__init__(**kwargs)
        print (self.log)

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
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=False)
    kept_out_at = Column(DateTime, nullable=False)
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
                'data-url': '/json?category=dungeon&filter={}'.format(
                    self.search_id),
                #'search_id': self.search_id,
                'columns': (
                    ('challenge_level', 'Difficulty'),
                    ('name', 'Name'),
                    ('dungeon_type', 'Dungeon Type'),
                ),
            },
        )

    def generate_main_panels(self):
        main_stats = []
        for k, v in self.frontend_columns:
            main_stats.append('{}: {}'.format(v, self.__getattribute__(k)))

        now = datetime.now()
        if now < self.opened_at:
            main_stats.append(
                '<span title="{}">{} will be available {}</span>'.format(
                    self.opened_at,
                    WORLD_TYPE[self.world_type],
                    naturaltime(self.opened_at)
                )
            )
        if now > self.closed_at:
            # All events seem to close_at three days after we are kept_out_at
            # even though there is no redemption period for "challenge" types
            main_stats.append(
                '<span title="{}">{} ended {}</span>'.format(
                    self.closed_at,
                    WORLD_TYPE[self.world_type],
                    naturaltime(self.closed_at)
                )
            )
        if now < self.kept_out_at and self.world_type == 2:
            main_stats.append(
                '<span title="{}">Event will end {}</span>'.format(
                    self.kept_out_at, naturaltime(self.kept_out_at)
                )
            )

        self._main_panels = (
            {
                'title': 'Main Stats',
                'items': main_stats,
                'footer': '*Time zones to be implemented.',
            },
        )

    def __init__(self, **kwargs):
        kwargs['world_type'] = kwargs['type']
        kwargs['opened_at'] = datetime.fromtimestamp(kwargs['opened_at'])
        kwargs['closed_at'] = datetime.fromtimestamp(kwargs['closed_at'])
        kwargs['kept_out_at'] = datetime.fromtimestamp(kwargs['kept_out_at'])
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

    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=False)
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
        self._main_panels.append(
            {
                'title': 'Preparation Recommendations',
                'body': 'Things you might want to bring to acheive specific\
 conditions',
                'items': ('Also spoiler these just in case',),
                'footer': '*To be implemented (hopefully).',
            }
        )
        battles = []
        total_stam = 0
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
        self._main_panels[0]['items'].append(
            'Total stamina required: {}'.format(total_stam))
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
        kwargs['opened_at'] = datetime.fromtimestamp(kwargs['opened_at'])
        kwargs['closed_at'] = datetime.fromtimestamp(kwargs['closed_at'])
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
            print ('{} has no battles'.format(dungeon))

def get_dungeons(content=None):
    '''
    Return a list of dungeons corresponding to a main content update.

    A content of 1 (or less) will return all dungeons.
    A null content or content greater than the number of content patches will
    return the latest batch only.
    '''
    if content == 'all':
        content = 0
    try:
        content = int(content)
    except ValueError:
        content = sys.maxsize
    except TypeError:
        content = sys.maxsize

    dungeons = []
    with session_scope() as session:
        # Filter out events first
        worlds = session.query(World).filter(World.world_type == 1)
        world_ids = (i.id for i in worlds)

        dungeon_query = session.query(Dungeon)\
                               .options(subqueryload(Dungeon.world))\
                               .options(subqueryload(Dungeon.prizes))\
                               .options(subqueryload(Dungeon.battles))\
                               .filter(Dungeon.world_id.in_(world_ids))\
                               .order_by(Dungeon.challenge_level, Dungeon.id)

        if content <= 1:
            # We want all the dungeons from the beginning
            dungeons = dungeon_query.all()
        else:
            # else we want to start from a specific content update
            # Sort and group the dungeons
            temp_dungeons = dungeon_query\
                .order_by('opened_at')\
                .group_by('opened_at').all()
            # If someone is asking for content from the future return the
            # latest content update only
            content = min(content, len(temp_dungeons))
            # Subtract one from the content number because we count the original
            # content as "1" and not "0"
            content -= 1
            # Get the datetime this update was released
            opened_at = temp_dungeons[content].opened_at
            # Now we can finally get all the dungeons released after this time
            dungeons = dungeon_query.filter(
                Dungeon.opened_at >= opened_at).all()
        session.expunge_all()

    return dungeons

class Battle(BetterBase):
    __tablename__ = 'battle'
    id = Column(Integer, primary_key=True, autoincrement=False)
    dungeon_id = Column(Integer, ForeignKey('dungeon.id'), nullable=False)
    name = Column(String(length=64), nullable=False)
    round_num = Column(TINYINT, nullable=False)
    has_boss = Column(Boolean, nullable=False)
    stamina = Column(TINYINT, nullable=False)

    enemies = relationship('Enemy', secondary=enemy_table, backref='battles')

    #conditions =
    # Will probably be a many to many backref

    def generate_main_panels(self):
        main_stats = []

        self._main_panels = [
            {
                'title': 'Main Stats',
                'items': main_stats + [
                    'Name: {}'.format(self.name),
                    'Dungeon: {}'.format(
                        '<a href=/"{}">{}</a>'.format(
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
        self._main_panels.append(
            {
                'title': 'Enemies',
                'body': '' if self.enemies else 'No items found in database.',
                'items': ('<a href="/{}">{}</a>'.format(
                    enemy.search_id, enemy) for enemy in self.enemies),
                'footer': 'These items are not all inclusive.'
            },
        )
        self._main_panels.append(
            {
                'title': 'Drops',
                'body': '' if self.drops else 'No items found in database.',
                'items': ('<a href="/{}">{} from {}</a>'.format(
                    drop.drop_id, drop.drop.name, drop.enemy
                ) for drop in self.drops),
                'footer': '*To be improved (maybe).',
            },
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
    # There are at least two different Enemy.filter(name == 'Behemoth')
    # Although unlike Flan there is not a Realm identifier in the name
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
    #def_attributes = relationship('Def_Attribute')
    exp = Column(SMALLINT, nullable=False)

    frontend_columns = (
        ('name', 'Name'),
        ('is_sp_enemy', 'Boss'),
    )

    def generate_main_panels(self):
        self._main_panels = (
            {
                'title': 'Main Stats',
                'items': [
                    'Name: {}'.format(self.name),
                ],
            },
            {
                'title': 'Resistances',
                'footer': '*To be implemented (hopefully).',
            },
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
                'search_id': self.search_id,
                'columns': (
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

    @property
    def search_id(self):
        return self.param_id

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


'''
class Def_Attribute(BetterBase):
    __tablename__ = 'def_attribute'
    id = Column(Integer, primary_key=True, autoincrement=False)
'''


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
                grade_panel['items'] = [
                    'Casts: {}'.format(grade.arg1),
                    'Creation/Enhancement cost: {}'.format(grade.required_gil),
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
            print ('\tAbility {} has additional args'.format(kwargs['name']))
        for i in (
            'category_id',  # id for category_name
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
    name = Column(String(length=32), nullable=True)

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
            new_log = Log(log='Add name to drop {}'.format(self))
            with session_scope() as session:
                session.add(new_log)
            # The session self is attached to will do the commit()

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

    category_name = Column(String(length=32), nullable=False)
    equipment_type = Column(TINYINT, nullable=False)    # 1:"Weapon", 2:"Armor", 3:"Accessory"
    # "category_id": 80,                                # Do I care?
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
            "category_id",
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

def import_dammitdame(filepath):
    print ('import_dammitdame("{}") start'.format(filepath))
    with session_scope() as session:
        pass
    print ('import_dammitdame("{}") end'.format(filepath))

def import_equipmentbuilder(filepath):
    print ('import_equipmentbuilder("{}")'.format(filepath))
    with session_scope() as session:
        pass
    print ('import_equipmentbuilder("{}")'.format(filepath))

def import_battle_list(data=None, filepath=''):
    '''
    /dff/world/battles
    '''
    print ('import_battle_list("{}") start'.format(filepath))
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
                new_log = Log(log='Add battle {}'.format(new_battle))
                session.add(new_log)
                #session.add_all((new_battle, new_log))
    success = True
    print ('import_battle_list("{}") end'.format(filepath))
    return success

def import_world(data=None, filepath=''):
    '''
    /dff/world/dungeons
    '''
    print ('import_world("{}") start'.format(filepath))
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
            new_log = Log(log='Add world {}'.format(new_world))
            session.add(new_log)
        for dungeon in data.get('dungeons', []):
            prizes = dungeon['prizes']
            new_dungeon = session.query(Dungeon).filter_by(
                id=dungeon['id']).first()
            if new_dungeon is None:
                new_dungeon = Dungeon(**dungeon)
                session.add(new_dungeon)
                session.commit()
                new_log = Log(log='Add dungeon {}'.format(new_dungeon))
                session.add(new_log)
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
                    new_log = Log(log='Add prize {} from {}'.format(
                        new_prize, new_dungeon))
                    session.add(new_log)
        success = True
    print ('import_world("{}") end'.format(filepath))
    return success

def import_battle(data=None, filepath=''):
    '''
    get_battle_init_data
    '''
    print ('import_battle("{}") start'.format(filepath))
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
                        id = drop.get('item_id')
                        if id is not None:
                            # Get the Drop or make a new one
                            new_drop = session.query(Drop).filter_by(
                                id=id).first()
                            if new_drop is None:
                                name = get_name_by_id(id)
                                if name == id:
                                    name = None
                                new_drop = Drop(id=id, name=name)
                            new_drops.append(new_drop)
                    # Get the unique enemy as per param_id and lv
                    # I do not think enemy_id matters 2015-05-01
                    enemy_id = e['enemy_id']
                    params = e['params']
                    if isinstance(params, dict):
                        params = (params,)
                    for p in params:
                        param_id = p['id']
                        lv = p['lv']
                        new_enemy = session.query(Enemy).filter_by(
                            enemy_id=enemy_id,
                            param_id=param_id,
                            lv=lv,
                        ).first()
                        if new_enemy is None:
                            # The enemy does not exist so make one!
                            event = battle.get('event')
                            if event is not None and isinstance(event, dict):
                                e['event_id'] = event.get('event_id')
                                e['event_type'] = event.get('event_type')
                            e['is_sp_enemy'] = enemy['is_sp_enemy']
                            e['params'] = p
                            new_enemy = Enemy(**e)
                            new_log = Log(log='Add enemy {}'.format(new_enemy))
                            session.add_all((new_enemy, new_log))
                            session.commit()
                        # Get the battle obj for the next steps
                        old_battle = session.query(Battle).filter_by(
                            id=battle_id).first()
                        if old_battle is None:
                            print ('We are missing a battle object for {}'
                                   .format(new_enemy))
                            # This may occur if we skip import_battle_list()
                            continue
                        # Associate the drops with the enemy/battle here
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
                                drop_association = DropAssociation(
                                    enemy_id=new_enemy.id,
                                    drop_id=new_drop.id,
                                    battle_id=old_battle.id,
                                )
                                session.add(new_drop)
                                session.add(drop_association)
                                session.commit()
                                new_log = Log(
                                    log='Add drop {}'.format(drop_association))
                                session.add(new_log)
                        if old_battle not in new_enemy.battles:
                            new_enemy.battles.append(old_battle)
                            new_log = Log(log='Add enemy {} to {}'.format(
                                new_enemy, old_battle))
                            session.add(new_log)
                        session.commit()
                        # TODO 2015-05-10
                        # Improve this nesting indentation
        success = True
    print ('import_battle("{}") end'.format(filepath))
    return success

def import_party(data=None, filepath=''):
    '''
    /dff/party/list
    '''
    print ('import_party("{}") start'.format(filepath))
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
            new_log = Log(log='Add relic {}'.format(new_relic))
            session.add_all((new_relic, new_log))
            session.commit()

        materials = data['materials']
        for m in materials:
            if session.query(session.query(Material).filter_by(
                    id=m['id']).exists()).scalar():
                continue
            new_material = Material(**m)
            new_log = Log(log='Add material {}'.format(new_material))
            session.add_all((new_material, new_log))
            session.commit()
        success = True
    print ('import_party("{}") end'.format(filepath))
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
        for grades in recipes.itervalues():
            for a in grades.itervalues():
                id = a['ability_id']
                grade = a['grade']
                new_ability = session.query(Ability).filter_by(
                    ability_id=id, grade=grade).first()
                if new_ability is None:
                    new_costs = []
                    for material_id, count in\
                        a['material_id_2_num'].iteritems():
                        with session.no_autoflush:
                            material = session.query(Material).filter_by(
                                id=material_id).one()
                        new_cost = AbilityCost(count=count)
                        new_cost.material = material
                        new_costs.append(new_cost)
                    new_ability = Ability(**a)
                    for new_cost in new_costs:
                        new_ability.materials.append(new_cost)
                    new_log = Log(log='Add ability {}'.format(new_ability))
                    session.add_all((new_ability, new_log))
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
        for e in (data['new_src_user_equipment'],
                  data['old_src_user_equipment'],):
            if check_exists(e.get('equipment_id'),
                            e.get('level'), e.get('rarity')):
                continue
            new_relic = Relic(**e)
            new_log = Log(log='Add {}'.format(new_relic))
            session.add_all((new_relic, new_log))
            session.commit()
        success = False
    return success


# Commented out because recordpeeker.handle_party_list() is superior.
'''
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

def get_by_id(id, all=False):
    r = None
    with session_scope() as session:
        for m, c, o in (
            (Material, Material.id, 'id'),
            (World, World.id, 'id'),
            (Dungeon, Dungeon.id, 'id'),
            (Ability, Ability.ability_id, 'name'),
            (Enemy, Enemy.param_id, 'lv'),
            (Relic, Relic.equipment_id, 'level'),
            (Battle, Battle.id, 'id'),
        ):
            # joinedload('*') is slow
            #q = session.query(m).filter(c == id).order_by(o).options(joinedload('*'))
            q = session.query(m).filter(c == id).order_by(o).options(subqueryload('*'))
            # lazyload('*') does not work the way I want it to work
            #q = session.query(m).filter(c == id).order_by(o).options(lazyload('*'))
            #q = session.query(m).filter(c == id).order_by(o)
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

def main():
    out = rank_relics()
    for k, v in out.items():
        print (k, v)

if __name__ == '__main__':
    main()


### EOF ###
