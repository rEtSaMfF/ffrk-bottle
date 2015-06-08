from webtest import TestApp, AppError
from sqlalchemy import inspect
from nose.tools import raises, assert_raises

import ffrkapp
import models.models as models

from models.base import engine
from models.battle import enemy_table
from models.condition import condition_table


class TestModels():
    def setUp(self):
        self.session = models.create_session()
        self.inspector = inspect(engine)

    def tearDown(self):
        self.session.close()

    def test_db(self):
        assert self.inspector.default_schema_name == 'ffrk'
        assert self.inspector.get_table_names()

    def test_query(self):
        assert self.session.query(models.AbilityCost).first()
        assert self.session.query(models.Ability).first()
        assert self.session.query(models.Log).first()
        assert self.session.query(models.World).first()
        assert self.session.query(models.Prize).first()
        assert self.session.query(models.Dungeon).first()
        assert self.session.query(models.Condition).first()
        assert self.session.query(condition_table).first()
        assert self.session.query(enemy_table).first()
        assert self.session.query(models.Battle).first()
        assert self.session.query(models.AttributeAssociation).first()
        assert self.session.query(models.Attribute).first()
        assert self.session.query(models.Enemy).first()
        #assert self.session.query(models.EnemyAbility).first()
        assert self.session.query(models.Drop).first()
        assert self.session.query(models.DropAssociation).first()
        assert self.session.query(models.Material).first()
        assert self.session.query(models.Relic).first()
        assert self.session.query(models.Character).first()
        assert self.session.query(models.CharacterEquip).first()
        assert self.session.query(models.CharacterAbility).first()
        assert self.session.query(models.Quest).first()


class TestFFRKApp():
    def setUp(self):
        self.app = TestApp(ffrkapp.app)
        self.url = ffrkapp.app.get_url

    def tearDown(self):
        pass

    def test_dungeons_json(self):
        resp = self.app.get(self.url('json_dungeons'))
        assert resp.status == '200 OK'
        assert resp.content_type == 'application/json'

        resp2 = self.app.get('{}?event=1'.format(self.url('json_dungeons')))
        assert resp2.status == '200 OK'
        assert resp2.content_type == 'application/json'

    def test_about_redirect(self):
        resp = self.app.get(self.url('home'))
        assert resp.status == '302 Found'

        about = resp.follow()
        assert about.status == '200 OK'

        soup = about.html
        assert soup.html.head.title.text == 'About'

    def test_404(self):
        path = '404.not.found'
        resp = self.app.get('/{}'.format(path), status=404)
        assert path in resp.text

    def test_static_404(self):
        resp = self.app.get(self.url('static', filepath='404.not.found'),
                            status=404)
        assert 'File does not exist.' in resp.text

    def test_post(self):
        pass

    def test_bad_post(self):
        pass


### EOF ###
