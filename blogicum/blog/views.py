from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post, User


NUM_POSTS_ON_PAGE = 10


def get_pub_posts():
    return Post.objects.select_related(
        'author',
        'category',
        'location',
    ).filter(
        pub_date__lte=datetime.now(),
        is_published=True,
        category__is_published=True
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class HomePageListView(ListView):
    model = Post
    queryset = get_pub_posts()
    template_name = 'blog/index.html'
    paginate_by = NUM_POSTS_ON_PAGE


class CategoryPostsListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = NUM_POSTS_ON_PAGE

    def get_queryset(self):
        return get_pub_posts().filter(
            category__slug=self.kwargs['category_slug']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            is_published=True,
            slug=self.kwargs['category_slug']
        )
        return context


class UserListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = NUM_POSTS_ON_PAGE

    def get_queryset(self):
        if self.request.user.username == self.kwargs['username']:
            posts = Post.objects.select_related(
                'author',
                'category',
                'location',
            )
        else:
            posts = get_pub_posts()
        return posts.filter(author__username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User, username=self.kwargs['username']
        )
        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):
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

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user}
        )


class PostMixin:
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'


class PostFormMixin(PostMixin):
    form_class = PostForm


class PostReverseMixin:
    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user}
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        return Post.objects.select_related(
            'author',
            'category',
            'location',
        )

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if self.request.user != post.author:
            return get_object_or_404(
                Post,
                pk=self.kwargs['post_id'],
                pub_date__lte=datetime.now(),
                is_published=True,
                category__is_published=True
            )
        else:
            return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related(
            'author'
        )
        return context


class PostCreateView(LoginRequiredMixin,
                     PostFormMixin,
                     PostReverseMixin,
                     CreateView
                     ):

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(OnlyAuthorMixin, PostFormMixin, UpdateView):

    def handle_no_permission(self):
        return redirect('blog:post_detail', self.get_object().pk)


class PostDeleteView(OnlyAuthorMixin,
                     PostMixin,
                     PostReverseMixin,
                     DeleteView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context


class CommentMixin(OnlyAuthorMixin):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id)


class CommentUpdateView(CommentMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(CommentMixin, DeleteView):
    pass

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.object.post_id}
                       )
