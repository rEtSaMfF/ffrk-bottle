from __future__ import absolute_import

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT, BIGINT
from sqlalchemy.orm import relationship

from .base import BetterBase, session_scope
from .condition import SpecificCondition


enemy_table = Table('enemy_table', BetterBase.metadata,
                    Column('enemy_id', Integer,
                           ForeignKey('enemy.id'), nullable=False),
                    Column('battle_id', BIGINT,
                            ForeignKey('battle.id'), nullable=False),
)

class Battle(BetterBase):
    __tablename__ = 'battle'
    id = Column(BIGINT, primary_key=True, autoincrement=False)
    dungeon_id = Column(BIGINT, ForeignKey('dungeon.id'), nullable=False)
    name = Column(String(length=64), nullable=False)
    round_num = Column(TINYINT, nullable=False)
    has_boss = Column(Boolean, nullable=False)
    stamina = Column(TINYINT, nullable=False)

    # TODO 2015-05-22
    # sort by Enemy.is_sp_enemy
    enemies = relationship('Enemy', secondary=enemy_table, backref='battles')

    # TODO 2015-05-19
    #messages = a many-to-many backref

    @property
    def specific_conditions(self):
        conditions = ()
        with session_scope() as session:
            conditions = session.query(SpecificCondition).filter(
                SpecificCondition.battle_id == self.id).all()
            session.expunge_all()
        return conditions

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

        conditions = self.specific_conditions
        conditions_count = 3 + len(conditions)
        conditions_body = None
        if conditions_count == 3:
            conditions_body = 'There are no specific conditions for this battle.\
'
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

            # Added with 2015-06-07 patch
            'sp_enemy_id',

            # Added with 2017-03-15 patch
            'play_mode',

            # Added with 2017-04-28 patch
            'show_timer_type',
        ):
            if i in kwargs:
                del(kwargs[i])

        super(Battle, self).__init__(**kwargs)

    def __repr__(self):
        return u'{}>{}'.format(self.dungeon, self.name)


### EOF ###
