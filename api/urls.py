from django.urls import path
from .views import *

urlpatterns = [
    path("topic/", TopicMessagesAPIView.as_view(), name="topics-messages"),
    path('messages/', UserChatsAPIView.as_view(), name='user-chats'),
]