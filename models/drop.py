from __future__ import absolute_import

import logging

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.mysql import BIGINT

from .base import BetterBase, session_scope
from .log import Log


class DropAssociation(BetterBase):
    __tablename__ = 'drop_table'
    enemy_id = Column(Integer, ForeignKey('enemy.id'), primary_key=True)
    drop_id = Column(Integer, ForeignKey('drop.id'), primary_key=True)
    battle_id = Column(BIGINT, ForeignKey('battle.id'), primary_key=True)

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
        return u'{} from {} in {}'.format(self.drop, self.enemy, self.battle)


class Drop(BetterBase):
    __tablename__ = 'drop'
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(length=32), default='')

    def __repr__(self):
        if self.name:
            return self.name
        return str(self.id)

    # TODO 2015-06-07
    # Fix the circular import
    def populate_name(self):
        from .models import get_name_by_id

        if self.name:
            return

        name = get_name_by_id(self.id)
        if name != self.id:
            self.name = name
            new_log = Log(log='Add name to Drop({})'.format(self))
            with session_scope() as session:
                session.add(new_log)
                session.commit()


def populate_drop_names():
    '''
    Get Drop() objects with no name and attempts to populate the name.
    This might run with cron.
    '''
    with session_scope() as session:
        drops = session.query(Drop).filter(Drop.name == '').all()
        for drop in drops:
            drop.populate_name()
            if not drop.name:
                logging.warning('Drop({}) still has no name.'.format(drop))


### EOF ###
