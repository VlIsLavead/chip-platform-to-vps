from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .serializers import *
from .services.topic_access import get_accessible_topics


class TopicMessagesAPIView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_active:
            raise PermissionDenied('Аккаунт отключен')
        
        profile = user.profile
        accessible_topics = get_accessible_topics(profile)

        try:
            topic = accessible_topics.get(id=self.kwargs['topic_id'])
        except Topic.DoesNotExist:
            raise PermissionDenied('Нет доступа к этому чату')

        return Message.objects\
                .filter(topic=topic) \
                .select_related('user', 'topic') \
                .order_by('created_at')


class UserChatsAPIView(generics.ListAPIView):
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_active:
            raise PermissionDenied('Аккаунт отключен')
        
        profile = user.profile
        topics = get_accessible_topics(profile)

        return topics \
                .prefetch_related('messages__user__user') \
                .distinct()