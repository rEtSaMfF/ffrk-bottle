from __future__ import absolute_import

import arrow

from sqlalchemy import Column, Integer, String
from sqlalchemy_utils import ArrowType
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT
from sqlalchemy.orm import relationship

from .base import BetterBase, session_scope, STRFTIME


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

            # Added with 2015-08-10 patch
            'series_formal_name',

            # Added with 2015-05-25 patch
            'has_brave_series_buddies',
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
                  .filter(World.kept_out_at > now).all()
        session.expunge_all()
    return events


### EOF ###
