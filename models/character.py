from __future__ import absolute_import

import json
import logging
import sys

from contextlib import contextmanager

from sqlalchemy import Column, Integer, String, or_
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT

from .base import BetterBase, session_scope


# TODO 2015-06-09
# Refactor Character and implement CharacterStat
# Include CharacterStat.last_updated


# TODO 2015-06-22
# Get these from battle.js
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
    'Gun': 15,

    'Ball': 30,
    'Hairpin': 31,
    #'Gunarm': ,
    #'Card': ,

    'Shield': 50,
    'Hat': 51,
    'Helm': 52,
    'Light Armor': 53,
    'Armor': 54,
    'Robe': 55,
    'Bracer': 56,

    'Accessory': 80,

    #'Weapon Upgrade': 98,
    #'Armor Upgrade': 99,

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
    'Bard': 14,
    'Dancer': 15,
    'Machinist': 16,
    'Darkness': 17,
    'Shooter': 19,
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
    14: 'Bard',
    15: 'Dancer',
    16: 'Machinist',
    17: 'Darkness',
    19: 'Shooter',
}

EQUIP_ID_NAME = {}
for k, v in CATEGORY_ID.items():
    if ABILITY_ID_NAME.get(v) == k:
        continue
    EQUIP_ID_NAME[v] = k
    EQUIP_ID_NAME[str(v)] = k

WEAPON = 1
ARMOR = 2
ACCESSORY = 3


class CharacterEquip(BetterBase):
    __tablename__ = 'character_equip'
    category_id = Column(TINYINT, primary_key=True, autoincrement=False)
    equipment_type = Column(TINYINT, primary_key=True, autoincrement=False)
    buddy_id = Column(Integer, primary_key=True, autoincrement=False)

    search_id = None

    def __init__(self, **kwargs):
        known_factor = '100'
        if str(kwargs['factor']) != known_factor:
            logging.critical(
                '{}.factor={} and not {} factor'.format(
                    type(self).__name__, kwargs['factor'], known_factor))

        self.category_id = int(kwargs['category_id'])

        for i in (
            'factor',
            'category_id',

            # Added with 2016-05-25 patch
            'is_extended',
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

    def dict(self):
        return {str(self):str(self)}

    #def jsonify(self):
        #return json.dumps({str(self):str(self)}, separators=(',',':'))
        #return '{"' + str(self) + '":"' + str(self) + '"}'


class CharacterAbility(BetterBase):
    __tablename__ = 'character_ability'
    category_id = Column(TINYINT, primary_key=True, autoincrement=False)
    rarity = Column(TINYINT, nullable=False)
    buddy_id = Column(Integer, primary_key=True, autoincrement=False)

    search_id = None

    def __init__(self, **kwargs):
        self.category_id = int(kwargs['category_id'])

        for i in (
            'name',
            'category_id',

            # Added with 2016-05-25 patch
            'is_extended',
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

    def dict(self):
        return {
            ABILITY_ID_NAME.get(self.category_id, self.category_id):
            self.rarity
        }

    '''
    def jsonify(self):
        return json.dumps(
            {
                ABILITY_ID_NAME.get(
                    self.category_id,
                    'Unknown AbilityCategory[{}]'.format(self.category_id)):
                self.rarity,
            },
            separators=(',',':'))
        #return '{"' + ABILITY_ID_NAME.get(
        #    self.category_id,
        #    'Unknown AbilityCategory[{}]'.format(self.category_id)) +\
        #    '":' + str(self.rarity) + '}'
    '''

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
        ('series_spd', 'RS SPD'),
    )

    @property
    def additional_columns(self):
        return (
            ('Equipment', self.get_equips()),
            ('Abilities', self.get_abilities()),
            #('Equipment', [str(i) for i in self.get_equips()]),
            #('Abilities', [str(i) for i in self.get_abilities()]),
        )

    main_tabs = (
        {
            'id': 'stats',
            'title': 'Stats',
            'columns': (
                ('image_path', 'Image'),
                ('name', 'Name'),
                ('series_id', 'Series'),
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
            )
        },
        {
            'id': 'abilities',
            'title': 'Abilities',
            'columns': (
                ('image_path', 'Image'),
                ('name', 'Name'),
                ('series_id', 'Series'),
            ) +
            #tuple((v, v) for k, v in sorted(ABILITY_ID_NAME.items()))
            tuple((v, v) for k, v in ABILITY_ID_NAME.items())
        },
        {
            'id': 'weapons',
            'title': 'Weapons',
            'columns': (
                ('image_path', 'Image'),
                ('name', 'Name'),
                ('series_id', 'Series'),
            ) +
            #tuple((v, v) for k, v in sorted(EQUIP_ID_NAME.items()) if\
            tuple((v, v) for k, v in EQUIP_ID_NAME.items() if\
                  isinstance(k, int) and k < 50)
        },
        {
            'id': 'armor',
            'title': 'Armor',
            'columns': (
                ('image_path', 'Image'),
                ('name', 'Name'),
                ('series_id', 'Series'),
            ) +
            #tuple((v, v) for k, v in sorted(EQUIP_ID_NAME.items()) if\
            tuple((v, v) for k, v in EQUIP_ID_NAME.items() if\
                  isinstance(k, int) and k >= 50)
        },
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

        # Added with 2016-01-21 patch
        # This code is slightly redundant but here for safety
        # TODO 2016-01-21
        # Create another function for this
        for i in (
            'sp_acc',
            'sp_atk',
            'sp_def',
            'sp_eva',
            'sp_hp',
            'sp_matk',
            'sp_mdef',
            'sp_mnd',
            'sp_spd',
        ):
            if i in kwargs:
                kwargs[i.replace('sp_', 'series_')] = kwargs[i]
                del(kwargs[i])


        for i in (
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

            'default_soul_strike_id',
            'ability_category',
            'equipment_category',
            'level_max',

            'def',
            'description',
            'name',
            'image_path',

            # Added with 2015-06-07 patch
            'record_materia_1_id',
            'record_materia_step',
            'series_level',
            'can_equip_record_materia_num',
            'evolution_num',

            # Added with 2015-08-10 patch
            'soul_strike_1_id',
            'soul_strike_2_id',
            'soul_strike_3_id',
            'soul_strike_4_id',
            'soul_strike_exp_map',

            # Added with 2015-12-14 patch
            'role_type',  # TODO make a column/field
            'role_type_name',

            # Added with 2015-01-21 patch
            'dress_record_name',
            'dress_record_id',
            'default_image_path',

            # Added with 2016-05-25 patch
            'sphere_skill_level',
            'brave_series_ids_map',

            # Added with 2017-03-15 patch
            'legend_materia_1_id',
            'legend_materia_2_id',

            # Added with 2017-04-27 patch
            'legend_materia_exp_map',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Character, self).__init__(**kwargs)

    def __repr__(self):
        return '{} ({})'.format(self.name, self.level)


def find_negative_stats():
    '''
    Return an iterable of Character objects with a negative stat.
    '''
    characters = []
    with session_scope() as session:
        q = session.query(Character)
        # Is there a better way to get a list of attributes?
        columns = (Character.hp, Character.atk, Character.defense,
                   Character.acc, Character.eva, Character.matk,
                   Character.mdef, Character.mnd, Character.spd
        )
        filters = (c <= 0 for c in columns)
        # https://stackoverflow.com/questions/7942547/using-or-in-sqlalchemy
        q = q.filter(or_(*filters))
        characters = q.all()
        session.expunge_all()
    return characters


### EOF ###
