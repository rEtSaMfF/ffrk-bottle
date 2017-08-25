from __future__ import absolute_import

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT, BIGINT

from .base import BetterBase
from .log import Log


PRIZE_TYPE = {
    1: 'Completion Reward',
    2: 'First Time Reward',
    3: 'Mastery Reward',
    4: 'Quest Reward',
    5: 'Solo? Raid Reward',
    6: 'Leader? Raid Reward',
    7: 'Time Bonus Reward',
}

class Prize(BetterBase):
    __tablename__ = 'prize'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=32), nullable=False)
    prize_type = Column(TINYINT, nullable=False)
    count = Column(Integer, nullable=False)

    drop_type = Column(String(length=16), nullable=False)
    drop_id = Column(Integer, ForeignKey('drop.id'), nullable=False)
    dungeon_id = Column(BIGINT, ForeignKey('dungeon.id'), nullable=True)
    quest_id = Column(Integer, ForeignKey('quest.id'), nullable=True)

    drop = relationship('Drop', backref=backref('prizes'))
    dungeon = relationship('Dungeon',
                           backref=backref('prizes',
                                           order_by='Prize.prize_type'))
    quest = relationship('Quest', backref=backref('prizes'))

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

            # Added with 2016-11 multiplayer patch
            'disp_order',

            # Added with 2017-08-24 patch
            'clear_battle_time',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Prize, self).__init__(**kwargs)

    def __repr__(self):
        return u'{} x{} ({})'.format(self.name, self.count,
                                    PRIZE_TYPE[int(self.prize_type)])


### EOF ###
