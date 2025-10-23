from rest_framework import serializers
from account.models import Message, Topic, Profile


class TopicMessagesInputSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    topic_id = serializers.IntegerField()


class MessageSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.user.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'user', 'text', 'created_at']


class UserChatsInputSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class TopicSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ['id', 'name', 'is_private', 'related_order_id', 'message_count', 'last_message']

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'text': last_message.text,
                'created_at': last_message.created_at,
                'user': last_message.user.user.username
            }
        return None
