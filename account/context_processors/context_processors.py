from ..models import Topic, UserTopic, Message


def user_role(request):
    if request.user.is_authenticated:
        role = request.user.profile.role.name
        return {'user_role': role}
    return {'user_role': None}


def unread_messages(request):
    if not request.user.is_authenticated:
        return {'has_unread_messages_by_order_id': {}}
    
    profile = request.user.profile
    unread_by_order = {}

    private_topics = Topic.objects.filter(
        is_private=True,
        usertopic__user=profile
    ).select_related('related_order')

    for topic in private_topics:
        order_id = topic.related_order_id
        if not order_id:
            continue

        user_topic = UserTopic.objects.filter(user=profile, topic=topic).first()
        if user_topic and user_topic.last_read_message:
            has_unread = Message.objects.filter(
                topic=topic,
                id__gt=user_topic.last_read_message.id
            ).exists()
        else:
            has_unread = Message.objects.filter(topic=topic).exists()

        if has_unread:
            unread_by_order[order_id] = True

    return {'has_unread_messages_by_order_id': unread_by_order}


def theme(request):
    theme = request.session.get('theme', 'light')
    
    if 'theme' not in request.session:
        if request.META.get('HTTP_USER_AGENT', '').lower() != 'djdt':
            if request.headers.get('Sec-CH-Prefers-Color-Scheme') == 'dark':
                theme = 'dark'
                request.session['theme'] = 'dark'
    
    return {
        'current_theme': theme,
        'theme_stylesheet': f'css/{theme}_theme.css'
    }