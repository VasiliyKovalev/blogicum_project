from django.urls import include, path

from . import views


app_name = 'blog'

post_url = [
    path(
        'create/',
        views.PostCreateView.as_view(),
        name='create_post'
    ),
    path('<int:post_id>/',
         views.PostDetailView.as_view(),
         name='post_detail'),
    path(
        '<int:post_id>/edit/',
        views.PostUpdateView.as_view(),
        name='edit_post'
    ),
    path(
        '<int:post_id>/delete/',
        views.PostDeleteView.as_view(),
        name='delete_post'
    ),
]

comment_url = [
    path(
        'comment/',
        views.CommentCreateView.as_view(),
        name='add_comment'
    ),
    path(
        'edit_comment/<int:comment_id>/',
        views.CommentUpdateView.as_view(),
        name='edit_comment'
    ),
    path(
        'delete_comment/<int:comment_id>/',
        views.CommentDeleteView.as_view(),
        name='delete_comment'
    ),
]

urlpatterns = [
    path('', views.HomePageListView.as_view(), name='index'),
    path(
        'category/<slug:category_slug>/',
        views.CategoryPostsListView.as_view(),
        name='category_posts'
    ),
    path('posts/', include(post_url)),
    path('posts/<int:post_id>/', include(comment_url))
]

urlpatterns += [
    path(
        'profile-edit/',
        views.UserUpdateView.as_view(),
        name='edit_profile'
    ),
    path(
        'profile/<str:username>/',
        views.UserListView.as_view(),
        name='profile'
    ),
]
