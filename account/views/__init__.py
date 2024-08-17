from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from ..forms import LoginForm, UserRegistrationForm, UserEditForm, ProfileEditForm, OrderEditForm
from ..models import Profile, Order


def user_login(request):
    if request.method != 'POST':
        form = LoginForm()
        return render(request, 'account/login.html', {'form': form})

    form = LoginForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        user = authenticate(request, username=cd['username'], password=cd['password'])

        if user is None:
            # TODO redirect to the login page with errors
            return HttpResponse('Invalid login')

        if not user.is_active:
            # TODO redirect to the login page with errors
            return HttpResponse('Disabled account')

        login(request, user)
        return redirect('/')


def user_logout(request):
    logout(request)
    return render(request, 'account/logged_out.html')


@login_required
def dashboard(request, message=''):
    profile = request.user.profile
    return {
        1: _dashboard_client,
        2: _dashboard_curator,
        3: _dashboard_executor,
    }[profile.role_id](request, message)


def _dashboard_client(request, message=''):
    orders = Order.objects.filter(creator_id=request.user.id)
    return render(
        request,
        'account/client/dashboard_client.html',
        {
            'section': 'dashboard',
            'data': {
                'orders': orders,
                'profile': {'company': 'рога и копыта'},
            }
        },
    )


@login_required
def new_order(request):
    if request.method == 'POST':
        order_form = OrderEditForm(request.POST, request.FILES)
        if order_form.is_valid():
            order_form.instance.creator = request.user.profile
            order_form.save(commit=True)
            return render(
                request,
                'account/client/new_order_success.html',
            )
        else:
            messages.error(request, 'Ошибка в заполнении данных для заказа')
    else:
        order_form = OrderEditForm()
    return render(
        request,
        'account/client/new_order.html',
        {
            'order_form': order_form,
        }
    )


def _dashboard_curator(request, message=''):
    return render(
        request,
        'account/dashboard_curator.html',
        {'section': 'dashboard', 'data': 'sample curator data'},
    )


def _dashboard_executor(request, message=''):
    return render(
        request,
        'account/dashboard_executor.html',
        {'section': 'dashboard', 'data': 'sample executor data'},
    )


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()

            Profile.objects.create(user=new_user, role_id=1)

            return render(
                request,
                'account/register_done.html',
                {'new_user': new_user}
            )
    else:
        user_form = UserRegistrationForm()
    return render(
        request,
        'account/register.html',
        {'user_form': user_form}
    )


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user,
                                 data=request.POST)
        profile_form = ProfileEditForm(
            instance=request.user.profile,
            data=request.POST,
            files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
        else:
            messages.error(request, 'Error updating your profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(
            instance=request.user.profile
        )
    return render(request,
                  'account/edit.html',
                  {'user_form': user_form,
                   'profile_form': profile_form})
