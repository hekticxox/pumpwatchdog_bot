import unittest
from db import (
    create_users_table,
    add_user,
    get_user_token,
    is_valid_token,
    renew_token,
    delete_user,
)
import os

class TestUserDB(unittest.TestCase):
    TEST_USER = "unittestuser"
    
    @classmethod
    def setUpClass(cls):
        # Ensure clean state
        create_users_table()
        # Remove user if exists
        delete_user(cls.TEST_USER)

    def test_add_and_get_user(self):
        token = add_user(self.TEST_USER, days_valid=1)
        self.assertIsInstance(token, str)
        fetched_token = get_user_token(self.TEST_USER)
        self.assertEqual(token, fetched_token)

    def test_token_validity(self):
        token = get_user_token(self.TEST_USER)
        self.assertTrue(is_valid_token(token))

    def test_renew_token(self):
        renewed = renew_token(self.TEST_USER, days_valid=2)
        self.assertTrue(renewed)
        token = get_user_token(self.TEST_USER)
        self.assertTrue(is_valid_token(token))

    def test_delete_user(self):
        deleted = delete_user(self.TEST_USER)
        self.assertTrue(deleted)
        token = get_user_token(self.TEST_USER)
        self.assertIsNone(token)

    @classmethod
    def tearDownClass(cls):
        # Cleanup after all tests
        delete_user(cls.TEST_USER)

if __name__ == "__main__":
    unittest.main()