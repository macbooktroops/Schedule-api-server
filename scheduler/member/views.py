from django.utils import timezone

from django.db.models import Q

from .models import UserProfile, User, FriendRequest

from .serializers import UserProfileSerializer, UserProfileCreateSerializer, FriendRequestSerializer, \
    EmailValidateSerializer, NicknameValidateSerializer, UserSerializer

from .exceptions import *

from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError


class UserProfileViewSet(mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    queryset = UserProfile.objects.all()

    def get_object(self) -> UserProfile:
        try:
            user_id = self.kwargs['pk']
            return UserProfile.objects.get(user__id=user_id)
        except (UserProfile.DoesNotExist, KeyError):
            raise DosNotExistUserException

    def get_serializer_class(self):
        if self.action == 'create':
            return UserProfileCreateSerializer
        else:
            return UserProfileSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            password = serializer.validated_data['user'].pop('password')
            serializer.validated_data['user'].pop('password2')
            user_profile = serializer.save()
            user_profile.user.set_password(password)
            user_profile.user.save()
            serializer.validated_data['user']['id'] = user_profile.user_id
        except (KeyError, AttributeError):
            return Response({
                'message': '회원가입 오류'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'message': '회원가입 성공',
                'user_info': serializer.validated_data
            }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_update(serializer)
        except Exception:
            return Response({
                'message': '정보 수정 오류'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            return Response({
                'message': '정보 수정 성공'
            }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def search(self, request):
        try:
            user = request.GET.get('name')
            user_profile = UserProfile.objects.get(user__nickname=user)
        except UserProfile.DoesNotExist:
            raise DosNotExistUserException
        else:
            user_data = {
                'email': user_profile.user.email,
                'username': user_profile.user.username,
                'nickname': user_profile.user.nickname,
                'birth': user_profile.birth,
            }

            return Response({
                'user': user_data,
            }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, url_path='friend-list')
    def friend_list(self, request, pk=None):
        user = self.get_object()
        friends_serializer = user.get_friends()
        return Response({
            'success': True,
            'data': {
                'friends': friends_serializer
            }
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, url_path='received-friend-request-list')
    # 나에게 친구 요청 보낸 유저 리스트
    def received_friend_request_list(self, request, pk=None):
        user = self.get_object().user
        request_users = [
            friend_request.request_user for friend_request in FriendRequest.objects.filter(
                assent=False,
                response_user=user
            ).select_related('request_user')
        ]
        request_user_data = UserSerializer(request_users, many=True).data

        return Response({'data': request_user_data})

    @action(methods=['GET'], detail=True, url_path='sent-friend-request-list')
    # 내가 친구 요청 보낸 유저 리스트
    def sent_friend_request_list(self, request, pk=None):
        user = self.get_object().user
        response_users = [
            friend_request.response_user for friend_request in FriendRequest.objects.filter(
                assent=False,
                request_user=user
            ).select_related('response_user')
        ]
        request_user_data = UserSerializer(response_users, many=True).data

        return Response({'data': request_user_data})


@api_view(['GET'])
def user_email_validate(request):
    data = {
        "email": request.GET.get('email')
    }
    serializer = EmailValidateSerializer(data=data)
    try:
        serializer.is_valid(raise_exception=True)
    except ValidationError:
        if serializer.errors['email'][0] == "user with this email already exists.":
            raise EmailUnique()
        elif serializer.errors['email'][0] == "Enter a valid email address.":
            raise EmailInvalid()
        elif serializer.errors['email'][0] == "This field may not be blank.":
            raise EmailBlank()
    else:
        raise EmailUseful()

    return Response({
        "message": "예상치 못한 오류"
    }, status=status.HTTP_417_EXPECTATION_FAILED)


@api_view(['GET'])
def user_nickname_validate(request):
    data = {
        "nickname": request.GET.get('nickname', "")
    }
    serializer = NicknameValidateSerializer(data=data)
    try:
        serializer.is_valid(raise_exception=True)
    except ValidationError:
        if serializer.errors['nickname'][0] == "user with this nickname already exists.":
            raise NicknameUnique()
        elif serializer.errors['nickname'][0] == "This field may not be blank.":
            raise NicknameBlank()
        elif serializer.errors['nickname'][0] == "Ensure this field has no more than 30 characters.":
            raise NicknameMaxLength()
    else:
        raise NicknameUseful()

    return Response({
        "message": "예상치 못한 오류"
    }, status=status.HTTP_417_EXPECTATION_FAILED)


class FriendRequestViewSet(mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer

    def create(self, request, *args, **kwargs):
        if request.data['request_user'] == request.data['response_user']:
            return Response({
                'message': '자기 자신에게는 친구 요청 불가'
            }, status=status.HTTP_409_CONFLICT)

        try:
            friend_request = FriendRequest.objects.get(
                Q(request_user=request.data['response_user'], response_user=request.data['request_user'])
                | Q(request_user=request.data['request_user'], response_user=request.data['response_user'])
            )
        except FriendRequest.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            return Response({
                'message': '친구 요청 보냄'
            }, status=status.HTTP_201_CREATED, headers=headers)

        if friend_request.assent:
            return Response({
                'message': '이미 친구 상태'
            }, status=status.HTTP_200_OK)

        if friend_request.request_user.id == int(request.data['request_user']):
            return Response({
                'message': '이미 친구 요청을 보냄'
            }, status=status.HTTP_202_ACCEPTED)
        else:
            friend_request.assent = True
            friend_request.assented_at = timezone.now()
            friend_request.save()

            request_user_profile = UserProfile.objects.get(user__id=int(request.data['request_user']))
            response_user_profile = UserProfile.objects.get(user__id=int(request.data['response_user']))

            req_user = request_user_profile.user
            res_user = response_user_profile.user

            request_user_profile.friends.add(res_user)
            request_user_profile.save()
            response_user_profile.friends.add(req_user)
            response_user_profile.save()

            return Response({
                'message': '친구 요청 수락',
            }, status=status.HTTP_200_OK)
