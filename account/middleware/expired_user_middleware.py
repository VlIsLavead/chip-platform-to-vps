from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now

def expired_user_middleware(get_response):
    def middleware(request):
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            if profile and profile.expiration_date and now() >= profile.expiration_date:
                if request.path != reverse('account_expired'):
                    return redirect('account_expired')

        response = get_response(request)
        return response
    return middleware