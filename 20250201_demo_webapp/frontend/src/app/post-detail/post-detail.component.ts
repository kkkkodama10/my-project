// src/app/post-detail/post-detail.component.ts
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PostService, Post, Comment, CreateComment } from '../services/post.service';

@Component({
  selector: 'app-post-detail',
  templateUrl: './post-detail.component.html',
  styleUrls: ['./post-detail.component.scss']
})
export class PostDetailComponent implements OnInit {
  post: Post | null = null;
  comments: Comment[] = [];
  newComment: CreateComment = { userId: 0, content: '' };
  liked: boolean = false;

  constructor(private route: ActivatedRoute, private postService: PostService) { }

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.loadPost(id);
    this.loadComments(id);
  }

  loadPost(id: number) {
    this.postService.getPost(id).subscribe(post => this.post = post);
  }

  loadComments(postId: number) {
    this.postService.getComments(postId).subscribe(comments => this.comments = comments);
  }

  toggleLike() {
    if (!this.post) return;
    if (this.liked) {
      this.postService.unlikePost(this.post.id).subscribe(() => {
        this.liked = false;
      });
    } else {
      this.postService.likePost(this.post.id).subscribe(() => {
        this.liked = true;
      });
    }
  }

  addComment() {
    if (!this.post || !this.newComment.content.trim()) return;
    this.postService.addComment(this.post.id, this.newComment).subscribe(comment => {
      this.comments.push(comment);
      this.newComment = { userId: 0, content: '' };
    });
  }
}
