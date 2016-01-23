from __future__ import absolute_import

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT
from sqlalchemy.orm import subqueryload

from .base import BetterBase, session_scope
from .drop import DropAssociation


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
                'footer': 'These locations are not all inclusive and the drop ra\
tes may vary.',
            },
        )

    def __init__(self, **kwargs):
        for i in (
            'image_path',
            'created_at',
            'num',

            # Added with 2016-01-21 patch
            'type',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Material, self).__init__(**kwargs)

    def __repr__(self):
        return '{}'.format(self.name)


### EOF ###
