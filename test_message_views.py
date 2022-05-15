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
        
        testUser1 = User.signup("test1", "test1@gmail.com", "passTest1", None)
        testUser1.id = 15
        
        testUser2 = User.signup("test2", "test2@gmail.com", "passTest2", None)
        testUser2.id = 18
        
        db.session.commit()
        
        testUser1 = User.query.get(testUser1.id)
        testUser2 = User.query.get(testUser2.id)
        
        self.testUser1 = testUser1
        self.testUser2 = testUser2

        self.client = app.test_client()


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
            
    def test_add_message_from_user_not_logged_in(self):
        """Test that a logged out user, can't add messsages"""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
                
    def test_view_message(self):
        """Test that a message can be viewed"""
        
        msg = Message(id = 1, text="Lorem ipsum...", user_id=self.testuser_id)
        
        db.session.add(msg)
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            msg = Message.query.get(1)

            resp = c.get(f'/messages/{msg.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(msg.text, str(resp.data))
        
    def test_invalid_message(self):
        """Test trying to access invalid message"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get('/messages/777')

            self.assertEqual(resp.status_code, 404)
            
    def test_remove_message(self):
        """Test removing a message"""
        msg = Message(id = 1, text="Lorem ipsum...", user_id=self.testuser_id)
        
        db.session.add(msg)
        db.session.commit()
        
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/1/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            msg = Message.query.get(1)
            self.assertIsNone(msg)
            
    def test_logged_out_user_remove_message(self):
        """Test that a logged out user can't delete message"""
        
        msg = Message(id = 1, text="Lorem ipsum...", user_id=self.testuser_id)

        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/1/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            msg = Message.query.get(1)
            self.assertIsNotNone(msg)
            
                    
            
    def test_unauthorized_user_remove_message(self):
        """Test that an unauthorized user cannot delete message"""        
        
        unAuthUser = User.signup(username="sketchy", email="sketchy@gmail.com", password="sket1234", image_url=None)
        unAuthUser.id = 666
        
        db.session.add(unAuthUser)
        db.session.commit()
        
        msg = Message(id = 1, text="Lorem ipsum...", user_id=self.testuser_id)
        
        db.session.add(msg)
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 666

            resp = c.post("/messages/1/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            msg = Message.query.get(1)
            self.assertIsNotNone(msg)

        
                
            

