"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

db.create_all()


app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Setup before test."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="tester",
                                    email="test@gmail.com",
                                    password="iamapassword",
                                    image_url=None)
        self.testuser_id = 1414
        self.testuser.id = self.testuser_id

        db.session.commit()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_without_session(self):
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_message_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 9999999999

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
    
    def test_message_show(self):

        msg = Message(
            id=12,
            text="test...",
            user_id=self.testuser_id
        )
        
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            msg = Message.query.get(12)

            resp = c.get(f'/messages/{msg.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(msg.text, str(resp.data))

    def test_invalid_message_show(self):
        """Should display 404 page"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get('/messages/9998887')

            self.assertEqual(resp.status_code, 404)

    def test_message_delete(self):

        m = Message(
            id=1234,
            text="testing",
            user_id=self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            m = Message.query.get(1234)
            self.assertIsNone(m)



    def test_message_delete_no_authentication(self):

        msg = Message(
            id=12,
            text="a test message",
            user_id=self.testuser_id
        )
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/12/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            msg = Message.query.get(12)
            self.assertIsNotNone(msg)
