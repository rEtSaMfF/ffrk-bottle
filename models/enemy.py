from __future__ import absolute_import

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT
from sqlalchemy.orm import relationship, subqueryload

from .base import BetterBase, session_scope


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
    226: 'Water Imp',
    227: 'Vanish',
    228: 'Porky',
    229: 'Sap',
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
    attribute_id = Column(SMALLINT, nullable=False)
    factor = Column(TINYINT, nullable=False)
    #name = Column(String(length=16))

    def __init__(self, **kwargs):
        super(Attribute, self).__init__(**kwargs)
        #self.name = ATTRIBUTE_ID.get(self.attribute_id, '')

    def __repr__(self):
        #return '{}: {}'.format(
        #    self.name, get_factor(self.attribute_id, self.factor))
        return '{}: {}'.format(
            ATTRIBUTE_ID.get(int(self.attribute_id), self.attribute_id),
            get_factor(self.attribute_id, self.factor)
        )

# NOTE 2015-05-27
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

    lv = Column(SMALLINT, nullable=False)
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

            # Added with 2015-02-14 patch
            'cast_time_type',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Enemy, self).__init__(**kwargs)

    def __repr__(self):
        return '{} ({})'.format(self.name, self.lv)


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


### EOF ###
