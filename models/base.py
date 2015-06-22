import decimal
import os
import json
import logging
import time
import traceback
import types

import arrow

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base as real_declarative_base
from sqlalchemy.orm import sessionmaker


### SQLALCHEMY INIT START ###
declarative_base = lambda cls: real_declarative_base(cls=cls)

@declarative_base
class BetterBase(object):
    '''
    Add some default properties and methods to the SQLAlchemy declarative base.
    '''
    @property
    def columns(self):
        '''
        Return all of the columns.
        '''
        return (c.name for c in self.__table__.columns)
        #return (c.key for c in class_mapper(self.__class__).columns)

    @property
    def frontend_columns(self):
        '''
        The columns we see when listing all objects of this class.
        An iterable of tuples (attribute_name, display_name).
        '''
        return ((c, c) for c in self.columns)

    @property
    def main_columns(self):
        '''
        The columns we see when listing similar objects of this class.
        An iterable of tuples (attribute_name, display_name).
        Example: listing the stats per level.
        '''
        return self.frontend_columns

    main_tabs = []
    # Will be an iterable of dicts representing different tabs on a category
    # such as a comparison of models.Character

    @property
    def search_id(self):
        '''
        The id used to search for this object using get_by_id().
        This ignores varying attributes such as stats per level.
        '''
        # My *_tables do not have an id attribute so this is an AttributeError.
        return self.id

    _main_panels = None
    # Will be an iterable of dicts representing this object on its main page.

    def generate_main_panels(self):
        self._main_panels = []

    @property
    def main_panels(self):
        if self._main_panels is None:
            self.generate_main_panels()

        return self._main_panels

    extra_tabs = []
    # Will be an iterable of dicts representing different pages used to display
    # objects similar to this object but differing slightly
    # (such as stats per level).

    additional_columns = ()
    # Will be an an iterable of tuples (key, attributes/properties)
    # to add to the dict representation.

    def __repr__(self):
        return u'{}({})'.format(self.__class__.__name__, self.columns)

    def dict(self):
        '''
        Transform the model into a dictionary.
        '''
        ret = dict((c, getattr(self, c)) for c in self.columns)
        if self.search_id is not None:
            ret['search_id'] = self.search_id
        for k, v in self.additional_columns:
            ret[k] = v
        return ret

    def jsonify(self):
        '''
        Transform the model into JSON.
        '''
        return json.dumps(self.dict(),
                          default=default_encode, separators=(',',':'))


def default_encode(obj):
    if isinstance(obj, decimal.Decimal):
        return u'{:.2f}'.format(self._value)
    if isinstance(obj, arrow.arrow.Arrow):
        return obj.for_json()
    if isinstance(obj, arrow.arrow.datetime):
        return arrow.get(obj).for_json()
        #return arrow.get(obj).timestamp
        #if obj.utcoffset() is not None:
        #    obj = obj - obj.utcoffset()

        #obj = obj.replace(tzinfo=None)
        #return (obj - arrow.arrow.datetime(1970, 1, 1)).total_seconds()
    if isinstance(obj, BetterBase):
        return obj.dict()
    if isinstance(obj, types.GeneratorType):
        return [i for i in obj]
    raise TypeError('{} is not JSON serializable'.format(obj))


engine = create_engine(
    'mysql+pymysql://{}:{}@{}:{}/{}'.format(
        os.environ['OPENSHIFT_MYSQL_DB_USERNAME'],
        os.environ['OPENSHIFT_MYSQL_DB_PASSWORD'],
        os.environ['OPENSHIFT_MYSQL_DB_HOST'],
        os.environ['OPENSHIFT_MYSQL_DB_PORT'],
        'ffrk',
    ), pool_recycle=3600)
create_session = sessionmaker(bind=engine)


# I do not use this plugin
'''
plugin = sqlalchemy.Plugin(
    engine,
    #Base.metadata,
    BetterBase.metadata,
    keyword='db',
    create=True,
    commit=True,
    use_kwargs=False
)
'''


@contextmanager
def session_scope():
    '''
    Provide a transactional scope around a series of operations.
    '''
    session = create_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(e, e.args)
        logging.error(traceback.print_exc())
        logging.error('exc_info=True', exc_info=True)
    finally:
        session.close()


# TODO 2015-05-08
# aaargh this
if False:
#if True:
    logging.basicConfig()
    logger = logging.getLogger('ffrk.sqltime')
    logger.setLevel(logging.DEBUG)

    @event.listens_for(Engine, 'before_cursor_execute')
    def before_cursor_execute(conn, cursor, statement,
                              parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
        logger.debug('Start Query: {}'.format(statement))

    @event.listens_for(Engine, 'after_cursor_execute')
    def after_cursor_execute(conn, cursor, statement,
                             parameters, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop(-1)
        logger.debug('Query Complete!')
        logger.debug('Total Time: {:f}'.format(total))


def make_tables():
    BetterBase.metadata.create_all(engine)
create_tables = make_tables
### SQLALCHEMY INIT END ###


### MODULE GLOBALS START ###
STRFTIME = '%Y-%m-%dT%H:%M:%S%z (%Z)'
### MODULE GLOBALS END ###


### EOF ###
