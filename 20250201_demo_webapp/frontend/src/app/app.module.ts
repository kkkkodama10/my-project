// src/app/app.module.ts
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http'; // ✅ 追加
import { RouterModule } from '@angular/router';

import { AppComponent } from './app.component';
import { UsersListComponent } from './users-list/users-list.component';
import { PostsListComponent } from './posts-list/posts-list.component';
import { PostDetailComponent } from './post-detail/post-detail.component';

@NgModule({
  declarations: [
    AppComponent,
    UsersListComponent,
    PostsListComponent,
    PostDetailComponent
  ],
  imports: [
    BrowserModule,
    FormsModule,
    HttpClientModule, // ✅ 追加
    RouterModule.forRoot([
      { path: 'users', component: UsersListComponent },
      { path: 'posts', component: PostsListComponent },
      { path: 'posts/:id', component: PostDetailComponent },
      { path: '', redirectTo: '/users', pathMatch: 'full' }
    ])
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
