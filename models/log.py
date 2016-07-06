from __future__ import absolute_import

import logging
import sys

import arrow

from sqlalchemy import Column, Integer, String
from sqlalchemy.types import TIMESTAMP

from .base import BetterBase


class Log(BetterBase):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(TIMESTAMP,
                       default=arrow.arrow.datetime.utcnow, nullable=False)
    log = Column(String(length=256), nullable=False)
    # I want a way to reference the objects in this log but that is not too easy

    frontend_columns = (
        ('timestamp', 'Timestamp'),
        ('log', 'Log'),
    )

    search_id = None

    def __init__(self, **kwargs):
        super(Log, self).__init__(**kwargs)
        try:
            logging.info(self.log)
        except (UnicodeEncodeError, ):
            logging.critical(UnicodeEncodeError)

    def __repr__(self):
        #return '{} {}'.format(self.timestamp, self.log)
        return '{} {}'.format(self.timestamp, self.log.encode(errors='ignore'))


### EOF ###
