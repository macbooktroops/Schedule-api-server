from rest_framework import serializers

from .models import UserProfile, User, FriendRequest


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'nickname', 'password')


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)
    class Meta:
        model = UserProfile
        fields = ('user', 'birth', 'language', )

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer.create(UserSerializer(), validated_data=user_data)
        user_profile = UserProfile.objects.create(user=user, birth=validated_data.pop('birth'), language=validated_data.pop('language'))

        return user_profile

    def update(self, instance, validated_data):
        user_data = validated_data['user']
        user = User.objects.get(id=instance.user_id)
        UserSerializer.update(UserSerializer(), instance=user, validated_data=user_data)

        instance.birth = validated_data.get('birth', instance.birth)
        instance.language = validated_data.get('language', instance.language)
        instance.save()

        return instance


class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = '__all__'