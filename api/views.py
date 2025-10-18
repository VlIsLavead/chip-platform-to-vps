from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from account.models import Profile, Order, Topic, Platform, Message
from .serializers import *


class TopicMessagesAPIView(APIView):
    def post(self, request):
        serializer = TopicMessagesInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        topic_id = serializer.validated_data["topic_id"]

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"error": "Неверный логин или пароль"}, status=401)
        if not user.is_active:
            return Response({"error": "Аккаунт отключен"}, status=403)

        profile = user.profile

        if profile.role.name == "Заказчик":
            users_in_company = Profile.objects.filter(company_name=profile.company_name).values_list("user", flat=True)
            orders = Order.objects.filter(creator__user__in=users_in_company)
            topics = Topic.objects.filter(related_order__in=orders)

        elif profile.role.name == "Куратор":
            topics = Topic.objects.all()

        elif profile.role.name == "Исполнитель":
            code_company = Platform.objects.get(platform_code=profile.company_name)
            orders = Order.objects.filter(platform_code_id=code_company)
            topics = Topic.objects.filter(related_order__in=orders)

        else:
            return Response({"error": "Нет доступа"}, status=403)

        try:
            topic = topics.get(id=topic_id)
        except Topic.DoesNotExist:
            return Response({"error": "Нет доступа к этому чату"}, status=403)

        messages = Message.objects.filter(topic=topic).select_related("user", "topic").order_by("created_at")

        output_serializer = MessageSerializer(messages, many=True)
        return Response(output_serializer.data, status=200)
    
    
class UserChatsAPIView(APIView):
    def post(self, request):
        serializer = UserChatsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"error": "Неверный логин или пароль"}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({"error": "Аккаунт отключен"}, status=status.HTTP_403_FORBIDDEN)

        profile = user.profile

        if profile.role.name == "Заказчик":
            users_in_company = Profile.objects.filter(company_name=profile.company_name)
            user_ids = users_in_company.values_list('user', flat=True)
            orders = Order.objects.filter(creator__user__in=user_ids)
            topics = Topic.objects.filter(related_order__in=orders)

        elif profile.role.name == "Куратор":
            topics = Topic.objects.all()

        elif profile.role.name == "Исполнитель":
            try:
                code_company = Platform.objects.get(platform_code=profile.company_name)
                orders = Order.objects.filter(platform_code_id=code_company)
                topics = Topic.objects.filter(related_order__in=orders)
            except Platform.DoesNotExist:
                return Response({"error": "Платформа не найдена"}, status=status.HTTP_403_FORBIDDEN)

        else:
            return Response({"error": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)

        topics = topics.prefetch_related(
            'messages__user__user'
        ).distinct()

        output_serializer = TopicSerializer(topics, many=True)
        
        return Response(output_serializer.data, status=status.HTTP_200_OK)