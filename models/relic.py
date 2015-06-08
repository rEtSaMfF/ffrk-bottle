from __future__ import absolute_import

import sys

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT
from sqlalchemy.orm import subqueryload

from .base import BetterBase, session_scope
from .drop import DropAssociation


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

    image_path = Column(String(length=64), nullable=False)
    detail_image_path = Column(String(length=64), nullable=False)
    description = Column(String(length=256), nullable=False)
    has_someones_soul_strike = Column(Boolean, nullable=False)
    has_soul_strike = Column(Boolean, nullable=False)
    soul_strike_id = Column(Integer, nullable=True)
    required_enhancement_base_gil = Column(SMALLINT, nullable=True)
    required_evolution_gil = Column(Integer, nullable=True)
    sale_gil = Column(SMALLINT, nullable=False)

    acc = Column(SMALLINT, nullable=False)
    hp = Column(SMALLINT, nullable=False)
    atk = Column(SMALLINT, nullable=False)
    critical = Column(SMALLINT, nullable=False)
    defense = Column(SMALLINT, nullable=False)
    eva = Column(SMALLINT, nullable=False)
    matk = Column(SMALLINT, nullable=False)
    mdef = Column(SMALLINT, nullable=False)
    mnd = Column(SMALLINT, nullable=False)
    series_acc = Column(SMALLINT, nullable=False)
    series_hp = Column(SMALLINT, nullable=False)
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
                'footer': 'These locations are not all inclusive and the drop ra\
tes may vary.',
            },
        )

    def __init__(self, **kwargs):
        name = kwargs['name']
        name = name.replace(u'\uff0b', '')
        name = name.encode(sys.stdout.encoding, errors='ignore')
        self.name = name
        self.defense = kwargs['def']
        self.image_path = kwargs['image_path'].replace('/dff', '')
        self.detail_image_path = kwargs['detail_image_path'].replace('/dff', '')

        for i in (
            'allowed_buddy_id',
            'atk_ss_point_factor',
            'def_ss_point_factor',
            'attributes',
            'can_evolve_now',
            'created_at',
            'exp',
            'is_sp_enhancement_material',
            'is_usable_as_enhancement_material',
            'is_usable_as_enhancement_src',
            'evol_max_level_of_base_rarity',
            'thumbnail_path',
            'id',

            'def',
            'name',
            'image_path',
            'detail_image_path',

            # Added with 2015-06-07 patch
            'is_accessory',
            'is_armor',
            'is_weapon',
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


### EOF ###
