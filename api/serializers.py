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
        

class TopicSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Topic
        fields = ['id', 'name', 'is_private', 'related_order_id', 'messages']
    

class UserChatsInputSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()