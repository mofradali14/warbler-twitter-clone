import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test user views"""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.tester = User.signup(username="tester",
                                    email="tester@gmail.com",
                                    password="apassword",
                                    image_url=None)
        self.tester_id = 948723
        self.tester.id = self.tester_id

        self.user_1 = User.signup("iamtest1", "test1@gmail.com", "testpassword", None)
        self.user_1_id = 72732
        self.user_1.id = self.user_1_id
        self.user_2 = User.signup("iamtest2", "test2@yahoo.com", "testpassword", None)
        self.user_2_id = 416
        self.user_2.id = self.user_2_id
        self.user_3 = User.signup("iamtest3", "test3@mail.com", "testpassword", None)
        self.user_4 = User.signup("iamtest4", "test4@gmail.com", "testpassword", None)

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def create_followers(self):
        follower1 = Follows(user_being_followed_id=self.user_1_id, user_following_id=self.tester_id)
        follower2 = Follows(user_being_followed_id=self.user_2_id, user_following_id=self.tester_id)
        follower3 = Follows(user_being_followed_id=self.tester_id, user_following_id=self.user_1_id)

        db.session.add_all([follower1,follower2,follower3])
        db.session.commit()

    def test_user_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@tester", str(resp.data))
            self.assertIn("iamtest1", str(resp.data))
            self.assertIn("iamtest2", str(resp.data))
            self.assertIn("iamtest3", str(resp.data))
            self.assertIn("iamtest4", str(resp.data))

    def test_search_user(self):
        with self.client as c:
            resp = c.get('/users?=iam')

            
            self.assertIn("@iamtest1", str(resp.data))
            self.assertIn("@iamtest2", str(resp.data))
            self.assertIn("@iamtest3", str(resp.data))
            self.assertIn("@iamtest4", str(resp.data))

    def test_show_user(self):
        with self.client as c:
            resp = c.get(f"/users/{self.tester_id}")
            self.assertEqual(resp.status_code, 200)
            
            self.assertIn("@tester", str(resp.data))


    def test_follows(self):

        self.create_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.tester_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@tester", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 0 messages
            self.assertIn("0", found[0].text)

            # Test for a count of 2 following
            self.assertIn("2", found[1].text)

            # Test for a count of 1 follower
            self.assertIn("1", found[2].text)
    
    def test_following(self):
        self.create_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.tester_id

            resp = c.get(f"/users/{self.tester_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@iamtest1", str(resp.data))
            self.assertIn("@iamtest2", str(resp.data))
            self.assertNotIn("@iamtest3", str(resp.data))

    def test_followers(self):

        self.create_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.tester_id

            resp = c.get(f"/users/{self.tester_id}/followers")

            self.assertIn("@iamtest1", str(resp.data))
            self.assertNotIn("@iamtest2", str(resp.data))
            self.assertNotIn("@iamtest3", str(resp.data))
    
    def test_bad_follow_access(self):
        self.create_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.tester_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@iamtest1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_bad_follower_access(self):
        self.create_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.tester_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@iamtest1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))