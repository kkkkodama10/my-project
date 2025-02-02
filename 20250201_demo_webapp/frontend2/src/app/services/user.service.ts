// src/app/services/user.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface User {
  id: number;
  username: string;
  createdAt: string;
}

@Injectable({
  providedIn: 'root'
})
export class UserService {
  // ※openapi jenerator の生成コードを利用する前提ですが、ここではシンプルな実装例です。
  private apiUrl = 'http://localhost:8080/users';

  constructor(private http: HttpClient) { }

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(this.apiUrl);
  }

  createUser(user: { username: string }): Observable<User> {
    return this.http.post<User>(this.apiUrl, user);
  }

  updateUser(user: User): Observable<User> {
    // API 定義に更新は含まれていませんが、仮に PATCH で更新すると想定
    return this.http.patch<User>(`${this.apiUrl}/${user.id}`, user);
  }

  deleteUser(id: number): Observable<any> {
    // API 定義に削除は含まれていませんが、仮に DELETE で削除すると想定
    return this.http.delete(`${this.apiUrl}/${id}`);
  }
}
