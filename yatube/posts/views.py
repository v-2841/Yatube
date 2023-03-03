from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .forms import PostForm, CommentForm, ProfileForm, GroupForm
from .models import Post, Group, User, Follow, Like, Comment, Membership
from .utils import paginator_func, ip_timezone_cookie, get_client_ip


def index(request):
    post_list = Post.objects.all()
    page_obj = paginator_func(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    if (request.COOKIES.get('timezone')
       and request.COOKIES.get('ip') == get_client_ip(request)):
        return render(request, 'posts/index.html', context)
    else:
        return ip_timezone_cookie(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginator_func(request, post_list)
    memberships = Membership.objects.filter(group=group)
    administrators_count = memberships.filter(role='a').count()
    members_count = memberships.count()
    if (request.user.is_authenticated
       and memberships.filter(member=request.user).exists()):
        membership = memberships.get(member=request.user)
    else:
        membership = None
    context = {
        'group': group,
        'page_obj': page_obj,
        'membership': membership,
        'administrators_count': administrators_count,
        'members_count': members_count,
    }
    return render(request, 'posts/group_posts.html', context)


@login_required
def group_create(request):
    form = GroupForm(
        request.POST or None,
    )
    if not form.is_valid():
        return render(request, 'posts/group_create.html', {'form': form})
    group = form.save(commit=False)
    group.save()
    group = Group.objects.get(slug=group.slug)
    group.members.add(request.user, through_defaults={'role': 'a'})
    return redirect('posts:group_posts', slug=group.slug)


@login_required
def group_edit(request, slug):
    group = get_object_or_404(Group, slug=slug)
    if Membership.objects.get(group=group, member=request.user).role != 'a':
        return redirect('posts:group_posts', slug=group.slug)
    form = GroupForm(
        request.POST or None,
        instance=group,
    )
    context = {
        'form': form,
        'is_edit': True
    }
    if not form.is_valid():
        return render(request, 'posts/group_create.html', context)
    form.save()
    return redirect('posts:group_posts', slug=group.slug)


@login_required
@require_http_methods(["POST"])
def group_delete(request, slug):
    group = get_object_or_404(Group, slug=slug)
    if Membership.objects.get(group=group, member=request.user).role != 'a':
        return redirect('posts:group_posts', slug=group.slug)
    group.delete()
    return redirect('posts:index')


@login_required
def group_follow(request, slug):
    group = get_object_or_404(Group, slug=slug)
    if not Membership.objects.filter(group=group,
                                     member=request.user).exists():
        Membership.objects.create(group=group, member=request.user)
    return redirect('posts:group_posts', slug=group.slug)


@login_required
def group_unfollow(request, slug):
    group = get_object_or_404(Group, slug=slug)
    if (Membership.objects.filter(group=group,
                                  member=request.user).exists()
        and Membership.objects.get(group=group,
                                   member=request.user).role != 'a'):
        Membership.objects.filter(group=group, member=request.user).delete()
    return redirect('posts:group_posts', slug=group.slug)


def group_administrators(request, slug):
    group = get_object_or_404(Group, slug=slug)
    administrators = group.members.filter(membership__role='a')
    context = {
        'group': group,
        'administrators': administrators,
    }
    return render(request, 'posts/group_administrators.html', context)


def group_members(request, slug):
    group = get_object_or_404(Group, slug=slug)
    members = group.members.all()
    context = {
        'group': group,
        'members': members,
    }
    return render(request, 'posts/group_members.html', context)


@login_required
def group_role_m(request, slug):
    group = get_object_or_404(Group, slug=slug)
    members = User.objects.filter(
        group=group, membership__role='m').order_by('username')
    context = {
        'group': group,
        'members': members,
    }
    return render(request, 'posts/group_role_m.html', context)


@login_required
def group_add_administrator(request, slug, username):
    group = get_object_or_404(Group, slug=slug)
    member = get_object_or_404(User, username=username)
    if (Membership.objects.filter(group=group,
                                  member=request.user).exists()
        and Membership.objects.get(group=group,
                                   member=request.user).role == 'a'
            and Membership.objects.filter(group=group,
                                          member=member).exists()):
        membership = Membership.objects.get(group=group, member=member)
        membership.role = 'a'
        membership.save()
    return redirect('posts:group_posts', slug=group.slug)


@login_required
def group_demote_administrator(request, slug):
    group = get_object_or_404(Group, slug=slug)
    if (Membership.objects.filter(group=group,
                                  member=request.user).exists()
        and Membership.objects.get(group=group,
                                   member=request.user).role == 'a'
            and Membership.objects.filter(group=group, role='a').count() > 1):
        membership = Membership.objects.get(group=group, member=request.user)
        membership.role = 'm'
        membership.save()
    return redirect('posts:group_posts', slug=group.slug)


def groups_list(request):
    context = {
        'groups': Group.objects.all().order_by('title'),
    }
    return render(request, 'posts/groups_list.html', context)


@login_required
def group_follow_index(request):
    groups = Group.objects.filter(
        members=request.user).values_list('slug', flat=True)
    post_list = Post.objects.filter(group__slug__in=groups)
    page_obj = paginator_func(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_follow_index.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    groups_count = Group.objects.filter(members=user).count()
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
        'groups_count': groups_count,
    }
    return render(request, 'posts/profile.html', context)


def profile_group_list(request, username):
    user = get_object_or_404(User, username=username)
    groups = Group.objects.filter(members=user).order_by('title')
    context = {
        'profile_user': user,
        'groups': groups,
    }
    return render(request, 'posts/profile_group_list.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    likes = post.likes.order_by('-created')[:settings.LIKES_VIEW_NUM]
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
        'likes_num': settings.LIKES_VIEW_NUM,
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
    return redirect('posts:post_detail',
                    post_id=request.user.posts.order_by('pk').last().id)


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
@require_http_methods(["POST"])
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    post.delete()
    return redirect('posts:profile', username=request.user)


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
def post_dislike(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Like.objects.filter(post=post, user=request.user).delete()
    return redirect('posts:post_detail', post_id=post_id)


def post_likes(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    context = {
        'post': post,
        'likes': post.likes.order_by('-created'),
    }
    return render(request, 'posts/post_likes.html', context)


def profile_followers(request, username):
    user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(author=user)
    context = {
        'profile_user': user,
        'followers': followers,
    }
    return render(request, 'posts/profile_followers.html', context)


def profile_followings(request, username):
    user = get_object_or_404(User, username=username)
    followings = Follow.objects.filter(user=user)
    context = {
        'profile_user': user,
        'followings': followings,
    }
    return render(request, 'posts/profile_followings.html', context)


@login_required
def profile_edit(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        return redirect('posts:profile', username=username)
    form = ProfileForm(
        request.POST or None,
        instance=user,
    )
    context = {
        'form': form,
    }
    if not form.is_valid():
        return render(request, 'posts/profile_edit.html', context)
    user.save()
    return redirect('posts:profile', username=username)


@login_required
def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return redirect('posts:post_detail', post_id=comment.post.id)
    form = CommentForm(
        request.POST or None,
        instance=comment
    )
    context = {
        'form': form,
    }
    if not form.is_valid():
        return render(request, 'posts/comment_edit.html', context)
    form.save()
    return redirect('posts:post_detail', post_id=comment.post.id)


@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return redirect('posts:post_detail', post_id=comment.post.id)
    if request.method == 'POST':
        comment.delete()
        return redirect('posts:post_detail', post_id=comment.post.id)
    return render(request,
                  'posts/comment_delete.html', {'comment': comment})
