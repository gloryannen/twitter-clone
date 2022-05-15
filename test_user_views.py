"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from cgitb import html
import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()
        
        self.testUser1 = User.signup("test1", "test1@gmail.com", "passTest1", None)
        self.testUser1_id = 15
        self.testUser1.id = self.testUser1_id
        
        self.testUser2 = User.signup("test2", "test2@gmail.com", "passTest2", None)
        self.testUser2_id = 18
        self.testUser2.id = self.testUser2_id
        
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_users_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))

    def test_users_search(self):
        with self.client as c:
            resp = c.get("/users?q=test")

            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))            

            self.assertNotIn("@notAUser", str(resp.data))
            

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testUser2_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test2", str(resp.data))

    
    def test_user_show_with_likes(self):
        msg1 = Message(id=24, text="Lorem ipsum...", user_id=self.testUser1_id)
        msg2 = Message(id=42, text="Test!", user_id=self.testUser2_id)
        msg3 = Message(id=43, text="Test test!", user_id=self.testUser2_id)
        msg4 = Message(id=44, text="Test test test!", user_id=self.testUser2_id)
        msg5 = Message(id=45, text="Test test test test!", user_id=self.testUser2_id)
        msg6 = Message(id=46, text="Test test test test test!", user_id=self.testUser2_id)
        
        db.session.add_all([msg1, msg2, msg3, msg4, msg5, msg6])
        db.session.commit()

        likesTest1 = Likes(user_id=self.testUser1_id, message_id=42)
        likesTest2 = Likes(user_id=self.testUser1_id, message_id=43)
        likesTest3 = Likes(user_id=self.testUser1_id, message_id=44)
        likesTest4 = Likes(user_id=self.testUser1_id, message_id=45)
        likesTest5 = Likes(user_id=self.testUser1_id, message_id=46)

        db.session.add_all([likesTest1, likesTest2, likesTest3, likesTest4, likesTest5])
        db.session.commit()

        with self.client as c:
            resp = c.get(f"/users/{self.testUser1_id}")
            
            self.assertIn("@test1", str(resp.data))
            
            # 5 for the num of likes
            self.assertIn("5", str(resp.data))

    def test_add_like(self):
        msg = Message(id=94, text="Lorem ipsum lorem ipsum lor...", user_id=self.testUser2_id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testUser1_id

            resp = c.post("/messages/94/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==94).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testUser1_id)

    def test_remove_like(self):
        msg1 = Message(id=24, text="Lorem ipsum...", user_id=self.testUser1_id)
        msg2 = Message(id=42, text="Test test test test!", user_id=self.testUser2_id)
        
        db.session.add_all([msg1, msg2])
        db.session.commit()

        likesTest = Likes(user_id=self.testUser1_id, message_id=42)

        db.session.add(likesTest)
        db.session.commit()

        m = Message.query.filter(Message.text=="Test test test test!").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testUser1_id)

        l = Likes.query.filter(
            Likes.user_id==self.testUser1_id and Likes.message_id==m.id
        ).one()

        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testUser1_id

            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 0)

    def test_unauthenticated_like(self):
        msg1 = Message(id=24, text="Lorem ipsum...", user_id=self.testUser1_id)
        msg2 = Message(id=42, text="Test test test test!", user_id=self.testUser2_id)
        
        db.session.add_all([msg1, msg2])
        db.session.commit()

        likesTest = Likes(user_id=self.testUser1_id, message_id=42)

        db.session.add(likesTest)
        db.session.commit()

        m = Message.query.filter(Message.text=="Test test test test!").one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

            self.assertEqual(like_count, Likes.query.count())

    def test_user_show_with_follows(self):
        f1 = Follows(user_being_followed_id=self.testUser2_id, user_following_id=self.testUser1_id)
        f2 = Follows(user_being_followed_id=self.testUser1_id, user_following_id=self.testUser2_id)

        db.session.add_all([f1,f2])
        db.session.commit()

        with self.client as c:
            resp = c.get(f"/users/{self.testUser1_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test1", str(resp.data))
            self.assertIn("1", str(resp.data))

    def test_show_following(self):
        f1 = Follows(user_being_followed_id=self.testUser2_id, user_following_id=self.testUser1_id)
        f2 = Follows(user_being_followed_id=self.testUser1_id, user_following_id=self.testUser2_id)

        db.session.add_all([f1,f2])
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testUser1_id

            resp = c.get(f"/users/{self.testUser1_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@test2", str(resp.data))
            self.assertNotIn("@notAUser", str(resp.data))

    def test_show_followers(self):
        f1 = Follows(user_being_followed_id=self.testUser2_id, user_following_id=self.testUser1_id)
        f2 = Follows(user_being_followed_id=self.testUser1_id, user_following_id=self.testUser2_id)

        db.session.add_all([f1,f2])
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testUser1_id

            resp = c.get(f"/users/{self.testUser1_id}/followers")

            self.assertIn("@test2", str(resp.data))
            self.assertNotIn("@notAUser", str(resp.data))

    def test_unauthorized_following_page_access(self):
        f1 = Follows(user_being_followed_id=self.testUser2_id, user_following_id=self.testUser1_id)
        f2 = Follows(user_being_followed_id=self.testUser1_id, user_following_id=self.testUser2_id)

        db.session.add_all([f1,f2])
        db.session.commit()
        
        with self.client as c:

            resp = c.get(f"/users/{self.testUser1_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@notAUser", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        f1 = Follows(user_being_followed_id=self.testUser2_id, user_following_id=self.testUser1_id)
        f2 = Follows(user_being_followed_id=self.testUser1_id, user_following_id=self.testUser2_id)

        db.session.add_all([f1,f2])
        db.session.commit()
        
        with self.client as c:

            resp = c.get(f"/users/{self.testUser1_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@notAUser", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))
