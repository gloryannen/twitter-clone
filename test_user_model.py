"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

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
        
        testUser2 = User.signup("test2", "test2@gmail.com", "passTest2", None)
        testUser2.id = 18
        
        db.session.commit()
        
        testUser1 = User.query.get(testUser1.id)
        testUser2 = User.query.get(testUser2.id)
        
        self.testUser1 = testUser1
        self.testUser2 = testUser2

        self.client = app.test_client()
        
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

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
    
    def test_user_repr(self):
        """Test repr method"""
        repr(self.testUser1)
        repr(self.testUser2)
        
    def test_user_is_following(self):
        """"Test user is following another user"""
        self.testUser1.following.append(self.testUser2)
        
        db.session.commit()
        
        self.assertEqual(len(self.testUser2.followers), 1)
        self.assertEqual(len(self.testUser2.following), 0)
        self.assertEqual(self.testUser1.following[0].id, self.testUser2.id)
        self.assertTrue(self.testUser1.is_following(self.testUser2))
        
        self.assertEqual(len(self.testUser1.followers), 0)
        self.assertEqual(len(self.testUser1.following), 1)
        self.assertEqual(self.testUser2.followers[0].id, self.testUser1.id)
        self.assertFalse(self.testUser2.is_following(self.testUser2))
        
    def test_user_signup(self):
        """Test user is successfully created"""
        newUser=User.signup("newUser", "newUser@gmail.com", "newPass1", None)
        newUser.id = 4
        
        db.session.commit()
        
        newUser = User.query.get(newUser.id)
        
        self.assertEqual(newUser.username, "newUser")
        self.assertEqual(newUser.email, "newUser@gmail.com")
        self.assertTrue(newUser.password.startswith("$2b$"))
        self.assertEqual(newUser.image_url, "/static/images/default-pic.png")
        
        
    def test_user_invalid_username_signup(self):
        """Test user signup failure on username"""
        failedUser=User.signup(None, "failedUser@gmail.com", "failedUsername", None)
        failedUser.id = 6
        with self.assertRaises(Exception) as context:
            db.session.commit()

    def test_user_invalid_password_signup(self):
        """Test user signup failure on password"""
        with self.assertRaises(ValueError) as context:
            User.signup("failedUser", "failedUser@gmail.com", None, None)

            
    def test_user_invalid_email_signup(self):
        """Test user signup failure on email"""
        failedUser=User.signup("failedUser", None, "failedEmail", None)
        failedUser.id = 12
        with self.assertRaises(Exception) as context:
            db.session.commit()
            
    def test_user_auth(self):
        """Test user authentication successfully"""
        testUser1 = User.authenticate(self.testUser1.username, "passTest1")
        self.assertEqual(testUser1.id, self.testUser1.id)
     
    def test_user_invalid_username_auth(self):
        """Test user authentication failure on username"""
        self.assertFalse(User.authenticate("failedUser", "passTest1"))
        
    def test_user_invalid_password_auth(self):
        """Test user authentication failure on password"""
        self.assertFalse(User.authenticate(self.testUser1.username, "failedPass"))    
        