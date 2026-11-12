from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import UserChangeForm

from .models import Post, Category, Comment
from .forms import CustomUserCreationForm, PostForm, CommentForm

User = get_user_model()


# --- ГЛАВНАЯ И КАТЕГОРИИ ---
def index(request):
    post_list = Post.objects.filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True)
    post_list = Post.objects.filter(
        category=category,
        pub_date__lte=timezone.now(),
        is_published=True
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/category.html',
                  {'category': category, 'page_obj': page_obj})


# --- ПРОФИЛЬ И РЕГИСТРАЦИЯ ---
def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.all().order_by('-pub_date')

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/profile.html',
                  {'profile_user': user, 'page_obj': page_obj})


class RegistrationView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('blog:index')


# --- ПОСТЫ (СОЗДАНИЕ, РЕДАКТИРОВАНИЕ, УДАЛЕНИЕ, ПРОСМОТР) ---
def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        post = get_object_or_404(
            Post, pk=post_id, pub_date__lte=timezone.now(),
            is_published=True, category__is_published=True
        )

    comments = post.comments.all()

    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = CommentForm()

    return render(request, 'blog/detail.html',
                  {'post': post, 'comments': comments, 'form': form})


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={
                       'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def test_func(self):
        return self.request.user == self.get_object().author

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def test_func(self):
        return self.request.user == self.get_object().author


# --- КОММЕНТАРИИ (РЕДАКТИРОВАНИЕ, УДАЛЕНИЕ) ---
class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def test_func(self):
        return self.request.user == self.get_object().author

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={
                       'post_id': self.kwargs['post_id']})


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def test_func(self):
        return self.request.user == self.get_object().author

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={
                       'post_id': self.kwargs['post_id']})


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserChangeForm
    template_name = 'blog/create.html'  # можно использовать тот же шаблон
    slug_url_kwarg = 'username'
    slug_field = 'username'

    def test_func(self):
        return self.request.user.username == self.kwargs['username']

    def get_success_url(self):
        return reverse('blog:profile', kwargs={
                       'username': self.object.username})
