from django.db import models
from django.db.models import Q, F
from django.contrib.auth import get_user_model

from .validators import validate_not_empty


User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    members = models.ManyToManyField(User, through='Membership')

    def __str__(self) -> str:
        return self.title


class Membership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    date_joined = models.DateField(auto_now_add=True)
    ROLES = (
        ('a', 'administrator'),
        ('m', 'member')
    )
    role = models.CharField(max_length=1, choices=ROLES, default='m')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'member'], name='only_one_sub'),
        ]


class Post(models.Model):
    text = models.TextField(
        db_index=True,
        validators=[validate_not_empty],
        verbose_name='Текст поста',
        help_text='Текст нового поста',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self) -> str:
        return self.text[:15]

    class Meta:
        ordering = ('-pub_date',)


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField()
    created = models.DateTimeField(
        auto_now_add=True,
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~Q(user=F('author')), name='anti_self_sub'),
            models.UniqueConstraint(
                fields=['user', 'author'], name='only_one_sub'),
        ]


class Like(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'], name='only_one_like'),
        ]
