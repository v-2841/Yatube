from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow, Like
from .utils import paginator_func


def index(request):
    post_list = Post.objects.all()
    page_obj = paginator_func(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginator_func(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    user_posts = user.posts.all()
    page_obj = paginator_func(request, user_posts)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=user).exists()
    context = {
        'author': user,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    likes = Like.objects.filter(post=post)
    liked = False
    if request.user.is_authenticated:
        liked = Like.objects.filter(
            post=post, user=request.user).exists()
    context = {
        'post': post,
        'form': CommentForm(request.POST),
        'comments': post.comments.all(),
        'liked': liked,
        'likes': likes,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'form': form,
        'is_edit': True
    }
    if not form.is_valid():
        return render(request, 'posts/create_post.html', context)
    form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    if request.method == 'POST':
        post.delete()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/delete_post.html', {'post_id': post_id})


@require_http_methods(["GET"])
def post_search(request):
    search_text = request.GET.get('search_text')
    if search_text is None:
        return redirect('posts:index')
    post_list = Post.objects.filter(text__icontains=search_text)
    page_obj = paginator_func(request, post_list)
    context = {
        'page_obj': page_obj,
        'search_text': search_text
    }
    return render(request, 'posts/post_search.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    authors = request.user.follower.values_list('author', flat=True)
    post_list = Post.objects.filter(author__id__in=authors)
    page_obj = paginator_func(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=user,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=user).delete()
    return redirect('posts:profile', username=username)


@login_required
def post_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Like.objects.get_or_create(
        post=post,
        user=request.user,
    )
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_unlike(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Like.objects.filter(post=post, user=request.user).delete()
    return redirect('posts:post_detail', post_id=post_id)
