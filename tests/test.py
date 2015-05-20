from webtest import TestApp

import wsgi.ffrkapp as ffrkapp
import wsgi.models as models

class TestModels():
    def setUp(self):
        self.session = models.create_session()

    def tearDown(self):
        self.session.close()

    def test_query(self):
        assert self.session.query(models.Relic).first()

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

    def test_about_redirect(self):
        resp = self.app.get(self.url('home'))
        assert resp.status == '302 Found'

        about = resp.follow()
        assert about.status == '200 OK'

        soup = about.html
        assert soup.html.head.title.text == 'About'


### EOF ###
