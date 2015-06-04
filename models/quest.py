from sqlalchemy import Column, Integer, String

from . import BetterBase

class Quest(BetterBase):
    __tablename__ = 'quest'
    id = Column(Integer, primary_key=True, autoincrement=False)

    def __init__(self, **kwargs):
        super(Quest, self).__init__(**kwargs)

    def __repr__(self):
        return type(self).__name__

### EOF ###
