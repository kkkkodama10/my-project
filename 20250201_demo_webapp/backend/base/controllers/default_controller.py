import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from base.models.comment import Comment  # noqa: E501
from base.models.create_comment import CreateComment  # noqa: E501
from base.models.create_post import CreatePost  # noqa: E501
from base.models.hello_get200_response import HelloGet200Response  # noqa: E501
from base.models.post import Post  # noqa: E501
from base.models.user import User  # noqa: E501
from base import util


def hello_get():  # noqa: E501
    """Returns a greeting message

     # noqa: E501


    :rtype: Union[HelloGet200Response, Tuple[HelloGet200Response, int], Tuple[HelloGet200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def posts_get():  # noqa: E501
    """Get all posts

     # noqa: E501


    :rtype: Union[List[Post], Tuple[List[Post], int], Tuple[List[Post], int, Dict[str, str]]
    """
    return 'do some magic!'


def posts_id_comments_get(id):  # noqa: E501
    """Get all comments for a post

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Union[List[Comment], Tuple[List[Comment], int], Tuple[List[Comment], int, Dict[str, str]]
    """
    return 'do some magic!'


def posts_id_comments_post(id, body):  # noqa: E501
    """Add a comment to a post

     # noqa: E501

    :param id: 
    :type id: int
    :param create_comment: 
    :type create_comment: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    create_comment = body
    if connexion.request.is_json:
        create_comment = CreateComment.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def posts_id_get(id):  # noqa: E501
    """Get a post by ID

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Union[Post, Tuple[Post, int], Tuple[Post, int, Dict[str, str]]
    """
    return 'do some magic!'


def posts_id_likes_delete(id):  # noqa: E501
    """Unlike a post

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def posts_id_likes_post(id):  # noqa: E501
    """Like a post

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def posts_post(body):  # noqa: E501
    """Create a new post

     # noqa: E501

    :param create_post: 
    :type create_post: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    create_post = body
    if connexion.request.is_json:
        create_post = CreatePost.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def users_get():  # noqa: E501
    """Get all users

     # noqa: E501


    :rtype: Union[List[User], Tuple[List[User], int], Tuple[List[User], int, Dict[str, str]]
    """
    return 'do some magic!'


def users_id_get(id):  # noqa: E501
    """Get a user by ID

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Union[User, Tuple[User, int], Tuple[User, int, Dict[str, str]]
    """
    return 'do some magic!'


def users_post(body):  # noqa: E501
    """Create a new user

     # noqa: E501

    :param user: 
    :type user: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    user = body
    if connexion.request.is_json:
        user = User.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
