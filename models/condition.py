from __future__ import absolute_import

from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.dialects.mysql import SMALLINT
from sqlalchemy.orm import relationship, backref

from .base import BetterBase


condition_table = Table('condition_table', BetterBase.metadata,
                    Column('battle_id', Integer,
                           ForeignKey('battle.id'), nullable=False),
                    Column('condition_id', Integer,
                           ForeignKey('condition.id'), nullable=False)
)

class Condition(BetterBase):
    __tablename__ = 'condition'
    id = Column(Integer, primary_key=True, autoincrement=True)
    condition_id = Column(SMALLINT, nullable=False)
    code_name = Column(String(length=32), nullable=False)
    title = Column(String(length=128), nullable=False)
    #medal_num = Column(TINYINT, nullable=False)

    battles = relationship('Battle',
                           secondary=condition_table,
                           backref=backref('conditions', lazy='subquery'))

    def __init__(self, **kwargs):
        kwargs['condition_id'] = kwargs['id']
        for i in (
            'id',
            'medal_num',

            # Added with 2015-06-07 patch
            'battle_specific_score_id',
        ):
            if i in kwargs:
                del(kwargs[i])

        super(Condition, self).__init__(**kwargs)

    def __repr__(self):
        return self.title


### EOF ###