from django.db import models

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    username = models.CharField(max_length=30)
    nickname = models.CharField(max_length=30, unique=True, null=False, blank=False)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nickname', ]


class UserProfile(models.Model):
    KOREAN = 'KR'
    ENGLISH = 'EN'

    LANGUAGE_CHOICES = (
        (KOREAN, 'Korean'),
        (ENGLISH, 'English'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birth = models.DateField(null=False, blank=False)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="KR", null=False)
    friends = models.ManyToManyField(User, related_name='userProfile_friends')

    def get_friends(self, *args, **kwargs):
        return self.friends.filter(**kwargs).values('id', 'username', 'nickname', *args)


class FriendRequest(models.Model):
    request_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_request_user')
    response_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_response_user')
    assent = models.BooleanField(null=False, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    assented_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "{} -> {}" .format(self.request_user, self.response_user)

    @classmethod
    def get_friend_request_list(cls, **kwargs):
        kwargs.pop('assent', None)
        user_columns = ['id', 'username', 'nickname']
        args = []
        if 'request_user' in kwargs:
            for c in user_columns:
                args.append("request_user__%s" % c)

        if 'response_user' in kwargs:
            for c in user_columns:
                args.append("response_user__%s" % c)

        return cls.objects.filter(assent=False, **kwargs).values(*args)
