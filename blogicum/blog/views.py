from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post, User


NUM_POSTS_ON_PAGE = 10


def get_posts_queryset(published=False, with_comments_count=False):
    posts = Post.objects.select_related(
        'author',
        'category',
        'location',
    )
    if published:
        posts = posts.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        )
    if with_comments_count:
        posts = posts.annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    return posts


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', self.get_object().pk)


class HomePageListView(ListView):
    template_name = 'blog/index.html'
    paginate_by = NUM_POSTS_ON_PAGE

    def get_queryset(self):
        return get_posts_queryset(
            published=True,
            with_comments_count=True
        )


class CategoryPostsListView(ListView):
    template_name = 'blog/category.html'
    paginate_by = NUM_POSTS_ON_PAGE

    def get_category_object(self):
        return get_object_or_404(
            Category,
            is_published=True,
            slug=self.kwargs['category_slug']
        )

    def get_queryset(self):
        return get_posts_queryset(
            published=True,
            with_comments_count=True
        ).filter(
            category=self.get_category_object()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category_object()
        return context


class ReverseToProfileMixin:

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class UserListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = NUM_POSTS_ON_PAGE

    def get_user_object(self):
        return get_object_or_404(
            User, username=self.kwargs['username']
        )

    def get_queryset(self):
        return get_posts_queryset(
            published=(
                self.request.user != self.get_user_object()
            ),
            with_comments_count=True
        ).filter(
            author=self.get_user_object()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_user_object()
        return context


class UserUpdateView(
    LoginRequiredMixin,
    ReverseToProfileMixin,
    UpdateView
):
    model = User
    template_name = 'blog/user.html'
    fields = (
        'username',
        'first_name',
        'last_name',
        'email',
    )

    def get_object(self, queryset=None):
        return self.request.user


class PostMixin:
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'


class PostDetailView(DetailView):
    queryset = get_posts_queryset(
        published=False,
        with_comments_count=False
    )
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if self.request.user != post.author and (
            post.pub_date > timezone.now()
            or not post.is_published
            or not post.category.is_published
        ):
            raise Http404
        else:
            return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related(
            'author'
        )
        return context


class PostCreateView(
    LoginRequiredMixin,
    PostMixin,
    ReverseToProfileMixin,
    CreateView
):
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(
    OnlyAuthorMixin,
    PostMixin,
    UpdateView
):
    form_class = PostForm

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk}
        )


class PostDeleteView(
    OnlyAuthorMixin,
    PostMixin,
    ReverseToProfileMixin,
    DeleteView
):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context


class CommentMixin:
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


class CommentReverseToPostMixin:

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post_id}
        )


class CommentCreateView(
    LoginRequiredMixin,
    CommentReverseToPostMixin,
    CreateView
):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_post_object(self):
        return get_object_or_404(
            Post,
            pk=self.kwargs['post_id']
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.get_post_object()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.get_post_object()
        return context


class CommentUpdateView(
    OnlyAuthorMixin,
    CommentMixin,
    CommentReverseToPostMixin,
    UpdateView
):
    form_class = CommentForm


class CommentDeleteView(
    OnlyAuthorMixin,
    CommentMixin,
    CommentReverseToPostMixin,
    DeleteView
):
    pass
