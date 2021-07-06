from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

User = get_user_model()


def index(request):
    """View-функция главной страницы.
    Выводит по 10 записей из всей базы
    """
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    """View-функция группы.
    Выводит по 10 записей выбранной группы slug
    """
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.all()
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'group': group, 'page': page}
    return render(request, 'group.html', context)


def profile(request, username):
    """View-функция профиля.
    Выводит по 10 записей выбранного пользователя
    """
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.all()
    count_posts = posts_list.count()
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'author': author, 'page': page, 'count': count_posts,
               'following': True}
    if not request.user.is_authenticated:
        return render(request, 'profile.html', context)
    author_followers = author.following.filter(user=request.user)
    if not author_followers.exists():
        context['following'] = False
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    """View-функция поста.
    Выводит выбранный пост post_id юзера username
    """
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.posts.all(), pk=post_id)
    comments = post.comments.all()
    count = author.posts.count()
    form = CommentForm(request.POST or None)
    context = {'post': post, 'author': author, 'count': count, 'form': form,
               'comments': comments}
    return render(request, 'post.html', context)


@login_required
def add_comment(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.posts.all(), pk=post_id)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return redirect('post', username, post_id)
    new_comment = form.save(commit=False)
    new_comment.author = request.user
    new_comment.post = post
    new_comment.save()
    return redirect('post', username, post_id)


@login_required
def new_post(request):
    """View-функция нового поста.
    На основе формы PostForm создаем новый пост
    """
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'new.html', {'form': form, 'new_post': True})
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect('index')


@login_required
def post_edit(request, username, post_id):
    """View-функция редактирования поста.
    На основе PostForm редактируется пост post_id юзера username
    """
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.posts.all(), pk=post_id)
    if author != request.user:
        return redirect('post', username, post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if not form.is_valid():
        return render(request, 'new.html',
                      {'form': form, 'post': post, 'new_post': False})
    form.save()
    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    """"Функция для отображения страницы подписок.
    Выводятся все посты авторов, на которых подписан юзер
    """
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    """Функция подписки юзера на автора username."""
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect('profile', username)
    Follow.objects.get_or_create(
        user=request.user,
        author=author
    )
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    """Функция отписки юзера от автора username."""
    author = get_object_or_404(User, username=username)
    author.following.all().filter(user=request.user).delete()
    return redirect('profile', username)


def page_not_found(request, exception):
    """View-функция страницы - ошибка 404. """
    return render(request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    """View-функция страницы - ошибка 500 """
    return render(request, 'misc/500.html', status=500)
