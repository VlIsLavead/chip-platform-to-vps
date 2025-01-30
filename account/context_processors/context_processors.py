def user_role(request):
    if request.user.is_authenticated:
        role = request.user.profile.role.name
        return {"user_role": role}
    return {"user_role": None}