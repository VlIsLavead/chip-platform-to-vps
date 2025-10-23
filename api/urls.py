from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import UserChatsAPIView, TopicMessagesAPIView


urlpatterns = [
    # JWT
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API
    path('chats/', UserChatsAPIView.as_view(), name='api-chats'),
    path('topics/<int:topic_id>/', TopicMessagesAPIView.as_view(), name='api-topic-messages'),
]