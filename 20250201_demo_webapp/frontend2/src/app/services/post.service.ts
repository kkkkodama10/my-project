// src/app/services/post.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Post {
  id: number;
  userId: number;
  content: string;
  createdAt: string;
}

export interface CreatePost {
  userId: number;
  content: string;
}

export interface Comment {
  id: number;
  postId: number;
  userId: number;
  content: string;
  createdAt: string;
}

export interface CreateComment {
  userId: number;
  content: string;
}

@Injectable({
  providedIn: 'root'
})
export class PostService {
  private postsUrl = 'http://localhost:8080/posts';

  constructor(private http: HttpClient) { }

  getPosts(): Observable<Post[]> {
    return this.http.get<Post[]>(this.postsUrl);
  }

  getPost(id: number): Observable<Post> {
    return this.http.get<Post>(`${this.postsUrl}/${id}`);
  }

  createPost(post: CreatePost): Observable<Post> {
    return this.http.post<Post>(this.postsUrl, post);
  }

  likePost(id: number): Observable<any> {
    return this.http.post(`${this.postsUrl}/${id}/likes`, {});
  }

  unlikePost(id: number): Observable<any> {
    return this.http.delete(`${this.postsUrl}/${id}/likes`);
  }

  getComments(postId: number): Observable<Comment[]> {
    return this.http.get<Comment[]>(`${this.postsUrl}/${postId}/comments`);
  }

  addComment(postId: number, comment: CreateComment): Observable<Comment> {
    return this.http.post<Comment>(`${this.postsUrl}/${postId}/comments`, comment);
  }
}
