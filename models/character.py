from __future__ import absolute_import

import sys
import logging

from contextlib import contextmanager

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT

from .base import BetterBase


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

            # Added 2015-06-07
            'record_materia_1_id',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Character, self).__init__(**kwargs)

    def __repr__(self):
        return '{} ({})'.format(self.name, self.level)


### EOF ###