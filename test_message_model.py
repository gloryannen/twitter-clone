"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


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
        
        testUser1 = User.signup("test1", "test1@gmail.com", "passTest1", None)
        testUser1.id = 15
        
        db.session.commit()
        
        self.testUser1 = User.query.get(testUser1.id)
        
        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic model work?"""
        
        msg = Message(text="Lorem ipsum...", user_id=self.testUser1.id)

        db.session.add(msg)
        db.session.commit()

        self.assertEqual(len(self.testUser1.messages), 1)
        self.assertEqual(self.testUser1.messages[0].text, "Lorem ipsum...")

    def test_message_likes(self):
        """Test that a user likes a message"""
        msg1 = Message(text="Lorem ipsum...", user_id=self.testUser1.id)
        msg2 = Message(text="Test test test test!", user_id=self.testUser1.id)
        
        db.session.add_all([msg1, msg2])
        db.session.commit()
        
        self.testUser1.likes.append(msg1)

        db.session.commit()

        l = Likes.query.filter(Likes.user_id == self.testUser1.id).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, msg1.id)