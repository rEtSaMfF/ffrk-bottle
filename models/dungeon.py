from __future__ import absolute_import

import sys

import arrow

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy_utils import ArrowType
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT
from sqlalchemy.orm import relationship, subqueryload, load_only

from .base import BetterBase, session_scope
from .world import World


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
    total_stamina = Column(SMALLINT, nullable=False)

    background_image_path = Column(String(length=64), nullable=False)
    prologue_image_path = Column(String(length=64), nullable=False)
    epilogue_image_path = Column(String(length=64), nullable=False)
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
        ('total_stamina', 'Total Stamina'),
        ('dungeon_type', 'Dungeon Type'),
    )

    def generate_main_panels(self):
        main_stats = []
        for k, v in self.frontend_columns:
            main_stats.append('{}: {}'.format(v, self.__getattribute__(k)))
        main_stats[-1] =\
            'Dungeon Type: {}'.format(DUNGEON_TYPE[self.dungeon_type])
        main_stats.insert(0, '<a href="/{}">{}</a>'.format(
            self.world.search_id, self.world))
        # TODO 2015-05-11
        # Copy the opened_at/closed_at items from World?

        self._main_panels = [
            {
                'title': 'Main Stats',
                'items': main_stats,
            },
        ]
        if self.prologue:
            self._main_panels.append(
                {
                    'title': 'Prologue',
                    'body': self.prologue,
                }
            )
        if self.epilogue:
            self._main_panels.append(
                {
                    'title': 'Epilogue',
                    'body': self.epilogue,
                }
            )
        battles = []
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
            if not battle.conditions:
                all_conditions_present = False
            for c in battle.conditions:
                conditions_count += 1
                # Filter out the standard conditions
                if c.condition_id not in (1001, 1002, 1004):
                    conditions.append(str(c))

        conditions_body = None
        if conditions_count == 0:
            conditions_body = 'We have not imported any conditions for this dungeon.'
            # Set this so that the 'footer' will be populated correctly
            all_conditions_present = False
        elif not all_conditions_present:
            conditions_body = 'We are missing some conditions for this dungeon.'
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
        self.dungeon_type = kwargs['type']
        self.opened_at = arrow.get(kwargs['opened_at'])
        self.closed_at = arrow.get(kwargs['closed_at'])
        self.epilogue = kwargs['epilogue'].encode(
            sys.stdout.encoding, errors='ignore')
        self.prologue = kwargs['prologue'].encode(
            sys.stdout.encoding, errors='ignore')
        self.background_image_path = kwargs['background_image_path'].replace(
            '/dff', '')
        self.prologue_image_path = kwargs['prologue_image_path'].replace(
            '/dff', '')
        self.epilogue_image_path = kwargs['epilogue_image_path'].replace(
            '/dff', '')

        for i in (
            'rank',
            'order_no',
            'is_new',
            'is_unlocked',
            'is_clear',
            'is_master',
            'bgm',

            'prizes',
            'type',
            'opened_at',
            'closed_at',
            'epilogue',
            'prologue',
            'background_image_path',
            'prologue_image_path',
            'epilogue_image_path',

            # Added with 2015-06-07 patch
            'captures',  # conditions
            'total_stamina',
            'button_style',
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


### EOF ###
