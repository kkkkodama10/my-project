// src/app/posts-list/posts-list.component.ts
import { Component, OnInit } from '@angular/core';
import { PostService, Post, CreatePost } from '../services/post.service';
import { Router } from '@angular/router';
import { UserService, User } from '../services/user.service';  // 登録済みユーザー取得用に追加

@Component({
  selector: 'app-posts-list',
  templateUrl: './posts-list.component.html',
  styleUrls: ['./posts-list.component.scss']
})
export class PostsListComponent implements OnInit {
  posts: Post[] = [];
  users: User[] = [];              // プルダウン用の登録ユーザー一覧
  newPost: CreatePost = {          // 新規投稿作成用オブジェクト
    userId: 0,
    content: ''
  };

  constructor(
    private postService: PostService, 
    private router: Router,
    private userService: UserService     // 依存性注入
  ) { }

  ngOnInit(): void {
    this.loadPosts();
    this.loadUsers();
  }

  loadPosts() {
    this.postService.getPosts().subscribe(posts => this.posts = posts);
  }

  loadUsers() {
    this.userService.getUsers().subscribe(users => this.users = users);
  }

  viewPost(post: Post) {
    this.router.navigate(['/posts', post.id]);
  }

  addPost() {
    // 入力内容のチェック: content が空でない、かつユーザーが選択されているか確認
    if (!this.newPost.content.trim() || this.newPost.userId === 0) return;

    this.postService.createPost(this.newPost).subscribe(createdPost => {
      // 作成成功後、リストに新しい投稿を追加
      this.posts.push(createdPost);
      // または、this.loadPosts(); で最新リストを再取得してもよい
      // フォームの入力値をクリア
      this.newPost = { userId: 0, content: '' };
    });
    this.loadPosts()
  }
}
