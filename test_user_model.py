"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        user_1 = User.signup("tester1", "number1@gmail.com", "iamapassword", None)
        user_id_1 = 1111
        user_1.id = user_id_1

        user_2 = User.signup("tester2", "number2@gmail.com", "iamapassword", None)
        user_id_2 = 2222
        user_2.id = user_id_2

        db.session.commit()

        user_1 = User.query.get(user_id_1)
        user_2 = User.query.get(user_id_2)

        self.user_1 = user_1
        self.user_id_1 = user_id_1

        self.user_2 = user_2
        self.user_id_2 = user_id_2

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()
        return super().tearDown()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_following(self):
        self.user_1.following.append(self.user_2)
        db.session.commit()

        self.assertEqual(len(self.user_1.followers), 0)
        self.assertEqual(len(self.user_2.followers),1)
        self.assertEqual(len(self.user_1.following), 1)
        self.assertEqual(len(self.user_2.following), 0)
        
        self.assertEqual(self.user_1.following[0], self.user_2)
        self.assertEqual(self.user_2.followers[0], self.user_1)

    def test_is_followed_by(self):
        self.user_1.following.append(self.user_2)
        db.session.commit()

        self.assertEqual(self.user_1.is_followed_by(self.user_2), False)
        self.assertEqual(self.user_2.is_followed_by(self.user_1), True)

    def test_is_following(self):
        self.user_1.following.append(self.user_2)
        db.session.commit()

        self.assertEqual(self.user_1.is_following(self.user_2), True)
        self.assertEqual(self.user_2.is_following(self.user_1), False)

    def test_user_signup(self):
        user = User.signup('tester', 'tester@gmail.com', 'iamapassword', None)
        user.id = 1414
        db.session.commit()

        user = User.query.get(1414)

        self.assertEqual(user.username, 'tester')
        self.assertEqual(user.id, 1414)
        self.assertEqual(user.email, 'tester@gmail.com')
        self.assertEqual(user.image_url, "/static/images/default-pic.png")
        self.assertEqual(user.bio, None)
        self.assertEqual(user.location, None)
        self.assertEqual(user.header_image_url, "/static/images/warbler-hero.jpg")

    def test_bad_user(self):
        bad_user = User.signup(None, "tester@gmail.com", "thisisapassword", None)
        uid = 9999999
        bad_user.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_bad_email(self):
        bad_email = User.signup("test", None, "thisisapassword", None)
        uid = 23479287
        bad_email.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_bad_password(self):
        with self.assertRaises(ValueError) as context:
            User.signup("tester", "test@gmail.com", None, None)
        with self.assertRaises(ValueError) as context:
            User.signup("tester", "test@gmail.com", "", None)

    
    def test_authentication(self):
        user = User.authenticate(self.user_1.username, "iamapassword")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user_id_1)
            
    def test_bad_user_authentication(self):
        self.assertFalse(User.authenticate("badaccountuser", "iamapassword"))

    def test_bad_password_authentication(self):
        self.assertFalse(User.authenticate(self.user_1.username, "wrongpassword"))