from __future__ import absolute_import

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.mysql import TINYINT, SMALLINT
from sqlalchemy.orm import relationship, backref

from .base import BetterBase, session_scope


class AbilityCost(BetterBase):
    __tablename__ = 'abilitycost'
    ability_id = Column(Integer, ForeignKey('ability.id'), primary_key=True)
    material_id = Column(Integer, ForeignKey('material.id'), primary_key=True)
    count = Column(TINYINT, nullable=False)

    material = relationship('Material',
                            backref=backref('abilities', lazy='select'),
                            #backref=backref('abilities', lazy='immediate'),
                            #backref=backref('abilities', lazy='joined'),
                            #backref=backref('abilities', lazy='subquery'),
                            #backref=backref('abilities', lazy='noload'),
                            #backref=backref('abilities', lazy='dynamic'),
                            #order_by='Ability.id',
    )
    ability = relationship('Ability',
                           backref=backref('materials', lazy='select'),
                           #backref=backref('materials', lazy='immediate'),
                           #backref=backref('materials', lazy='joined'),
                           #backref=backref('materials', lazy='subquery'),
                           #backref=backref('materials', lazy='noload'),
                           #backref=backref('materials', lazy='dynamic'),
    )

    def __init__(self, **kwargs):
        super(AbilityCost, self).__init__(**kwargs)

    def __repr__(self):
        return '{} {}'.format(self.count, self.material)


class Ability(BetterBase):
    __tablename__ = 'ability'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ability_id = Column(Integer, nullable=False)
    name = Column(String(length=32), nullable=False)
    description = Column(String(length=256), nullable=False)

    rarity = Column(TINYINT, nullable=False)
    category_id = Column(TINYINT, nullable=False)
    category_name = Column(String(length=32), nullable=False)
                  # ('Spellblade', 'Celerity', 'Combat', etc.)
    category_type = Column(TINYINT, nullable=False)
                  # {1:Physical, 2:White, 3:Black, 4:Summon, 5:Other}
    target_range = Column(TINYINT, nullable=False)
                  # {1:Single, 2:AOE, 3:Self}

    grade = Column(TINYINT, nullable=False)
    next_grade = Column(TINYINT, nullable=False)
    max_grade = Column(TINYINT, nullable=False)
    arg1 = Column(TINYINT, nullable=False)  # Number of casts
    #arg2 = Column(TINYINT, nullable=False)  # Unknown (all are zero)
    #arg3 = Column(TINYINT, nullable=False)  # Unknown (all are zero)
    required_gil = Column(Integer, nullable=False)
    sale_gil = Column(SMALLINT, nullable=False)

    frontend_columns = (
        ('name', 'Name'),
        ('rarity', 'Rarity'),
        ('category_name', 'Category'),
        ('category_type', 'Category Type'),
    )

    main_columns = frontend_columns + (('grade', 'Grade'), ('arg1', 'Casts'),)

    def generate_main_panels(self):
        main_stats = []
        for k, v in self.frontend_columns:
            main_stats.append('{}: {}'.format(v, self.__getattribute__(k)))
        main_stats.append('Target Range: {}'.format(self.target_range))

        self._main_panels = [
            {
                'title': 'Main Stats',
                'body': self.description if self.description else '',
                'items': main_stats,
            },
        ]

        with session_scope() as session:
            # The self.materials backref does not help here
            # because they are only applicable to this self.id
            # and not to the self.ability_id
            grades = session.query(Ability).filter_by(
                ability_id=self.ability_id).order_by(
                    'grade').all()
            for grade in grades:
                grade_panel = {'title': 'Grade {}'.format(grade.grade)}
                gil = grade.required_gil
                if gil is None or gil == 32767:
                    gil = 'Unknown'
                grade_panel['items'] = [
                    'Casts: {}'.format(grade.arg1),
                    'Creation/Enhancement cost: {}'.format(gil),
                    'Sale gil: {}'.format(grade.sale_gil),
                ]
                for cost in grade.materials:
                    grade_panel['items'].append(
                        '<a href="/{}">{}: {} Orbs</a>'.format(
                            cost.material.search_id, cost.material, cost.count)
                    )
                self._main_panels.append(grade_panel)

        self._main_panels.append(
            {
                'title': 'Total required',
                'footer': '*To be implemented (maybe).',
            }
        )

    @property
    def search_id(self):
        return self.ability_id

    def __init__(self, **kwargs):
        if kwargs['arg2'] or kwargs['arg3']:
            logging.critical(
                'Ability {} has additional args'.format(kwargs['name']))
        for i in (
            'arg2',  # all zero
            'arg3',  # all zero
            'factor_category',  # all one
            'command_icon_path',
            'image_path',
            'thumbnail_path',
            'material_id_2_num',
        ):
            if i in kwargs:
                del(kwargs[i])
        super(Ability, self).__init__(**kwargs)

    def __repr__(self):
        return '[{}*] {} {}/{}'.format(
            self.rarity, self.name, self.grade, self.max_grade)


### EOF ###
