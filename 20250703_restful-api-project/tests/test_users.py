import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
#

from flask import Flask, jsonify
import unittest
from src.app import app

class TestUsersEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_get_users(self):
        response = self.app.get('/v1/users')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    def test_get_users_empty(self):
        response = self.app.get('/v1/users')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

    def test_get_users_error(self):
        # Simulate an error scenario if needed
        response = self.app.get('/v1/users?error=true')
        self.assertEqual(response.status_code, 500)

if __name__ == '__main__':
    unittest.main()