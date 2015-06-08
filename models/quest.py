from __future__ import absolute_import

import json
import logging
import sys

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT

from .base import BetterBase, session_scope
from .drop import Drop
from .log import Log
from .prize import Prize


QUEST_PRIZE_TYPE = 4

class Quest(BetterBase):
    __tablename__ = 'quest'
    id = Column(Integer, primary_key=True, autoincrement=False)
    title = Column(String(length=64), nullable=False)
    description = Column(String(length=1024), nullable=False)
    achieve_cond_description = Column(String(length=128), nullable=False)
    achieve_type = Column(TINYINT, nullable=False)
    achieve_type_name = Column(String(length=16), nullable=False)

    hint_title = Column(String(length=128), nullable=False)
    hint_msg = Column(String(length=512), nullable=False)

    frontend_columns = (
        ('title', 'Title'),
        ('description', 'Description'),
    )

    @property
    def name(self):
        return self.title

    def generate_main_panels(self):
        self._main_panels = [
            {
                'title': self.title,
                'body': self.description,
            },
            {
                'title': 'Prizes',
                'items': self.prizes,
            },
        ]

    def __init__(self, **kwargs):
        self.description = kwargs['description'].encode(
            sys.stdout.encoding, error='ignore')
        for i in (
            'can_challenge',
            'disp_number',
            'is_achieved',
            'is_completed',
            'is_new',
            'is_tutorial',
            'prizes',

            'order_cond_description',
            'is_special',
            'is_challenging',

            # This is the recipe for "Create Ability" quests
            'ability_recipes',

            'description',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Quest, self).__init__(**kwargs)

    def __repr__(self):
        return self.title


def import_quests(data=None, filepath=''):
    '''
    /dff/quest/list
    '''
    logging.debug('{}(filepath="{}") start'.format(
        sys._getframe().f_code.co_name, filepath))
    if data is None or not isinstance(data, dict):
        if not filepath:
            raise ValueError('One kwarg of data or filepath is required.')
        with open(filepath) as infile:
            data = json.load(infile)

    if data.get('special_quest_prizes'):
        logging.critical('There is a special quest prize!')

    success = False
    with session_scope() as session:
        for quest in data['quests']:
            prizes = quest['prizes']
            new_quest = session.query(Quest)\
                               .filter(Quest.id == quest['id']).first()
            if new_quest is None:
                new_quest = Quest(**quest)
                new_log = Log(log='Create {}({})'.format(
                    type(new_quest).__name__, new_quest))
                session.add_all((new_quest, new_log))
                session.commit()
            for prize in prizes:
                id = prize['id']
                name = prize['name']
                drop = session.query(Drop).filter(
                    Drop.id == id).first()
                if drop is None:
                    drop = Drop(id=id, name=name)
                old_prize = session.query(Prize).filter(
                    Prize.drop_id == id,
                    Prize.prize_type == QUEST_PRIZE_TYPE,
                    Prize.quest == new_quest).first()
                if old_prize is not None:
                    continue
                prize['drop_id'] = id
                prize['prize_type'] = QUEST_PRIZE_TYPE
                new_prize = Prize(**prize)
                new_prize.drop = drop
                new_prize.quest = new_quest
                #session.add(new_prize)
                #session.flush()
                new_log = Log(log='Create {}({}) from {}({})'.format(
                    type(new_prize).__name__, new_prize,
                    type(new_quest).__name__, new_quest))
                #session.add(new_log)
                session.add_all((new_prize, new_log))
                session.commit()
        success = True
    logging.debug('{}(filepath="{}") end'.format(
        sys._getframe().f_code.co_name, filepath))
    return success

### EOF ###
