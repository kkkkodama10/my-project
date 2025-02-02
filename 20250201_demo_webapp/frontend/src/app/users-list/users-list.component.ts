// src/app/users-list/users-list.component.ts
import { Component, OnInit } from '@angular/core';
import { UserService, User } from '../services/user.service';

@Component({
  selector: 'app-users-list',
  templateUrl: './users-list.component.html',
  styleUrls: ['./users-list.component.scss']
})
export class UsersListComponent implements OnInit {
  users: User[] = [];
  newUser: { username: string } = { username: '' };
  editingUser: User | null = null;
  editedUsername: string = '';

  constructor(private userService: UserService) { }

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers() {
    this.userService.getUsers().subscribe(users => this.users = users);
  }

  addUser() {
    if (!this.newUser.username.trim()) return;
  
    this.userService.createUser(this.newUser).subscribe(() => {
      this.newUser.username = ''; // 入力欄をクリア
      this.loadUsers(); // ✅ 最新のユーザーリストを取得
    });
  }

  deleteUser(user: User) {
    this.userService.deleteUser(user.id).subscribe(() => {
      this.users = this.users.filter(u => u.id !== user.id);
    });
  }

  editUser(user: User) {
    // 編集モードに切り替え
    this.editingUser = { ...user };
    this.editedUsername = user.username;
  }

  updateUser() {
    if (this.editingUser) {
      const updatedUser: User = { ...this.editingUser, username: this.editedUsername };
      this.userService.updateUser(updatedUser).subscribe(user => {
        const index = this.users.findIndex(u => u.id === user.id);
        if (index !== -1) {
          this.users[index] = user;
        }
        this.editingUser = null;
      });
    }
  }

  cancelEdit() {
    this.editingUser = null;
  }
}
