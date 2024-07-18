from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .forms import CommentForm, PostForm, UserForm
from .models import Category, Comment, Post, User


NUM_POSTS_ON_PAGE = 10


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'


class CommentMixin(OnlyAuthorMixin):
    model = Comment
    template_name = 'blog/comment.html'


def get_pub_posts():
    return Post.objects.select_related(
        'author',
        'category',
        'location',
    ).filter(
        pub_date__lte=datetime.now(),
        is_published=True,
        category__is_published=True
    )


def paginate_page(request, posts):
    paginator = Paginator(posts, NUM_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


class HomePageListView(ListView):
    model = Post
    queryset = get_pub_posts()
    template_name = 'blog/index.html'
    paginate_by = NUM_POSTS_ON_PAGE


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = get_pub_posts().filter(
        category=category
    )
    page_obj = paginate_page(request, posts)
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/category.html', context)


def profile(request, username):
    profile = get_object_or_404(
        User,
        username=username
    )
    if request.user == profile:
        posts = Post.objects.select_related(
            'author',
            'category',
            'location',
        ).filter(author=profile.id)
    else:
        posts = get_pub_posts().filter(
            author=profile.id
        )
    page_obj = paginate_page(request, posts)
    context = {
        'profile': profile,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


class UserUpdateView(LoginRequiredMixin, UpdateView,):
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
            'blog:post_detail',
            kwargs={'pk': self.kwargs['pk']}
        )

@login_required
def edit_profile(request):
    form = UserForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', request.user)
    context = {'form': form}
    return render(request, 'blog/user.html', context)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related(
            'author'
        )
        return context


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user})


class PostUpdateView(OnlyAuthorMixin, PostMixin, UpdateView):

    def handle_no_permission(self):
        return redirect('blog:post_detail', self.get_object().pk)


def delete_post(request, pk):
    instance = get_object_or_404(Post, pk=pk, author=request.user)
    form = PostForm(instance=instance)
    context = {'form': form}
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:profile', instance.author)
    return render(request, 'blog/create.html', context)


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

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.object.post_id})
