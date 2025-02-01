import unittest

from flask import json

from server.models.comment import Comment  # noqa: E501
from server.models.create_comment import CreateComment  # noqa: E501
from server.models.create_post import CreatePost  # noqa: E501
from server.models.hello_get200_response import HelloGet200Response  # noqa: E501
from server.models.post import Post  # noqa: E501
from server.models.user import User  # noqa: E501
from server.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_hello_get(self):
        """Test case for hello_get

        Returns a greeting message
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/hello',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_posts_get(self):
        """Test case for posts_get

        Get all posts
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/posts',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_posts_id_comments_get(self):
        """Test case for posts_id_comments_get

        Get all comments for a post
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/posts/{id}/comments'.format(id=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_posts_id_comments_post(self):
        """Test case for posts_id_comments_post

        Add a comment to a post
        """
        create_comment = {"userId":0,"content":"content"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/posts/{id}/comments'.format(id=56),
            method='POST',
            headers=headers,
            data=json.dumps(create_comment),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_posts_id_get(self):
        """Test case for posts_id_get

        Get a post by ID
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/posts/{id}'.format(id=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_posts_id_likes_delete(self):
        """Test case for posts_id_likes_delete

        Unlike a post
        """
        headers = { 
        }
        response = self.client.open(
            '/posts/{id}/likes'.format(id=56),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_posts_id_likes_post(self):
        """Test case for posts_id_likes_post

        Like a post
        """
        headers = { 
        }
        response = self.client.open(
            '/posts/{id}/likes'.format(id=56),
            method='POST',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_posts_post(self):
        """Test case for posts_post

        Create a new post
        """
        create_post = {"userId":0,"content":"content"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/posts',
            method='POST',
            headers=headers,
            data=json.dumps(create_post),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_users_get(self):
        """Test case for users_get

        Get all users
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/users',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_users_id_get(self):
        """Test case for users_id_get

        Get a user by ID
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/users/{id}'.format(id=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_users_post(self):
        """Test case for users_post

        Create a new user
        """
        user = {"createdAt":"2000-01-23T04:56:07.000+00:00","id":0,"username":"username"}
        headers = { 
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/users',
            method='POST',
            headers=headers,
            data=json.dumps(user),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
