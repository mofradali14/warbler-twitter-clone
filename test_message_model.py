import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Setup prior test."""
        db.drop_all()
        db.create_all()

        self.uid = 123
        user = User.signup("testuser", "test@gmail.com", "iamapassword", None)
        user.id = self.uid
        db.session.commit()

        self.user = User.query.get(self.uid)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic model work?"""
        
        msg1 = Message(
            text="test message",
            user_id=self.uid
        )

        msg2 = Message(text="next test message", user_id=self.uid)

        db.session.add(msg1)
        db.session.add(msg2)
        db.session.commit()

        self.assertEqual(len(self.user.messages), 2)
        self.assertEqual(self.user.messages[0].text, "test message")
        self.assertEqual(self.user.messages[1].text, "next test message")

    def test_message_likes(self):
        msg1 = Message(
            text="test 1",
            user_id=self.uid
        )

        msg2 = Message(
            text="test 2",
            user_id=self.uid 
        )

        user = User.signup("testlikes", "testlikes@email.com", "iamapassword", None)
        uid = 1234
        user.id = uid
        db.session.add(msg1)
        db.session.add(msg2)
        db.session.add(user)

        db.session.commit()

        user.likes.append(msg1)

        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == uid).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, msg1.id)
        user.likes.append(msg2)
        db.session.commit()
        likes2 = Likes.query.filter(Likes.user_id == uid).all()
        self.assertEqual(len(likes2), 2)
        self.assertEqual(likes2[1].message_id, msg2.id)


        