// src/app/posts-list/posts-list.component.ts
import { Component, OnInit } from '@angular/core';
import { PostService, Post } from '../services/post.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-posts-list',
  templateUrl: './posts-list.component.html',
  styleUrls: ['./posts-list.component.scss']
})
export class PostsListComponent implements OnInit {
  posts: Post[] = [];

  constructor(private postService: PostService, private router: Router) { }

  ngOnInit(): void {
    this.loadPosts();
  }

  loadPosts() {
    this.postService.getPosts().subscribe(posts => this.posts = posts);
  }

  viewPost(post: Post) {
    this.router.navigate(['/posts', post.id]);
  }
}
