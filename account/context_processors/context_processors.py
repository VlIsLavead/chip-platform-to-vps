from ..models import Topic, UserTopic, Message

def user_role(request):
    if request.user.is_authenticated:
        role = request.user.profile.role.name
        return {"user_role": role}
    return {"user_role": None}

def unread_messages(request):
    if not request.user.is_authenticated:
        return {'has_unread_messages': False}
    
    profile = request.user.profile
    has_unread = False
    
    private_topics = Topic.objects.filter(
        is_private=True,
        usertopic__user=profile
    )
    
    for topic in private_topics:
        last_read_message = UserTopic.objects.filter(user=profile, topic=topic).first()
        if last_read_message and last_read_message.last_read_message:
            unread_count = Message.objects.filter(
                topic=topic,
                id__gt=last_read_message.last_read_message.id
            ).count()
            if unread_count > 0:
                has_unread = True
                break
    
    return {'has_unread_messages': has_unread}

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