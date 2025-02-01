import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from server.models.comment import Comment  # noqa: E501
from server.models.create_comment import CreateComment  # noqa: E501
from server.models.create_post import CreatePost  # noqa: E501
from server.models.hello_get200_response import HelloGet200Response  # noqa: E501
from server.models.post import Post  # noqa: E501
from server.models.user import User  # noqa: E501
from server import util

import logging
logger = logging.getLogger(__name__)

from database.db_helper import DBHelper


def hello_get():  # noqa: E501
    """Returns a greeting message

     # noqa: E501


    :rtype: Union[HelloGet200Response, Tuple[HelloGet200Response, int], Tuple[HelloGet200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def posts_get():  # noqa: E501
    """Get all posts
    """
    db = DBHelper()  # DBHelperインスタンスを作成
    try:
        rows = db.get_all_posts()  # これは Row オブジェクトのリストと想定

        # Row オブジェクトを dict に変換する例
        # もし rows が単一の Row なら、適宜対応するように修正してください。
        result = []
        for row in rows:
            # row["id"], row["content"] のようにキーアクセスできるなら dict() 変換可能
            result.append(dict(row))  # または row._asdict() など

        return result, 200

    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}, 500

    finally:
        db.close()
        
def posts_post(body):  # noqa: E501
    """Create a new post

     # noqa: E501

    :param create_post: 
    :type create_post: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    db = DBHelper()  # DBHelperインスタンスを作成
    try:
        # リクエストボディがJSONの場合、CreatePostオブジェクトに変換
        if connexion.request.is_json:
            create_post = CreatePost.from_dict(connexion.request.get_json())  # noqa: E501
        else:
            return {"message": "Invalid input format"}, 400

        # 必須フィールドのチェック
        if not create_post.user_id or not create_post.content:
            return {"message": "user_id and content are required"}, 400

        # データベースに新しいポストを追加
        post_id = db.add_post(create_post.user_id, create_post.content)

        # 成功レスポンスを返す
        return {"message": "Post created successfully", "post_id": post_id}, 201

    except Exception as e:
        # エラーハンドリング
        return {"message": f"An error occurred: {str(e)}"}, 500

    finally:
        db.close()  # データベース接続を閉じる


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


def users_get():  # noqa: E501
    """
    Get all users
    """
    db = DBHelper()  # DBHelperインスタンスを作成
    try:
        rows = db.get_all_users()  # これは Row オブジェクトのリストと想定

        result = []
        for row in rows:
            # row["id"], row["content"] のようにキーアクセスできるなら dict() 変換可能
            result.append(dict(row))  # または row._asdict() など

        return result, 200

    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}, 500


def users_id_get(id_):  # noqa: E501
    """
    Get a user by ID
    """
    db = DBHelper()
    try:
        row = db.get_user(id_)  # 単一Row or None を想定
        if row is None:
            return {"message": f"User with ID {id_} not found"}, 404

        # Row → dict へ変換
        user_dict = dict(row)
        return user_dict, 200

    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}, 500


def users_post(body):  # noqa: E501
    """
    Create a new user
    """
    db = DBHelper()  # DBHelperインスタンスを作成
    try:
        # リクエストボディがJSONの場合、CreatePostオブジェクトに変換
        if connexion.request.is_json:
            create_users = User.from_dict(connexion.request.get_json())  # noqa: E501
        else:
            return {"message": "Invalid input format"}, 400
        # 必須フィールドのチェック
        if not create_users.username:
            return {"message": "username and content are required"}, 400
        # データベースに新しいポストを追加
        post_id = db.create_user(create_users.username)

        # 成功レスポンスを返す
        return {"message": "Post created successfully", "post_id": post_id}, 201

    except Exception as e:
        # エラーハンドリング
        return {"message": f"An error occurred: {str(e)}"}, 500

    finally:
        db.close()  # データベース接続を閉じる
