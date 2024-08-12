from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import formset_factory
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
def dashboard(request):
    profile = request.user.profile
    return {
        1: _dashboard_client,
        2: _dashboard_curator,
        3: _dashboard_executor,
    }[profile.role_id](request)


def _dashboard_client(request):

    order_get = list(Order.objects.filter().values())
    print(order_get)

    OrderFormSet = formset_factory(OrderEditForm, max_num=len(order_get)-1)

    empty = """<div>
    <label for="id_form-__prefix__-platform_code">Код площадки:</label>



<select name="form-__prefix__-platform_code" id="id_form-__prefix__-platform_code">
  <option value="" selected></option>

</select>

</div>

  <div>
    <label for="id_form-__prefix__-order_type">Тип заказа:</label>



<select name="form-__prefix__-order_type" id="id_form-__prefix__-order_type">
  <option value="">""</option>


</select>

</div>

  <div>
    <label for="id_form-__prefix__-order_date">""</label>



<input type="text" name="form-__prefix__-order_date" id="id_form-__prefix__-order_date">

</div>

  <div>
    <label for="id_form-__prefix__-runtime">Срок выполнения по договору:</label>



<input type="text" name="form-__prefix__-runtime" id="id_form-__prefix__-runtime">

</div>

  <div>
    <label for="id_form-__prefix__-payment_status">Статус оплаты:</label>



<input type="checkbox" name="form-__prefix__-payment_status" id="id_form-__prefix__-payment_status">

</div>

  <div>
    <label for="id_form-__prefix__-order_status">Статус заказа:</label>



<select name="form-__prefix__-order_status" id="id_form-__prefix__-order_status">
  <option value="CTP" selected>Проверка топологии</option>

  <option value="PSF">Формирование запуска</option>

  <option value="PRD">Производство</option>

  <option value="SHP">Отгрузка</option>

  <option value="SHD">Отгружен</option>

</select>



</div>
"""
    OrderFormSet.empty_form = empty
    order_formset = OrderFormSet(initial=list(order_get))
    print(order_formset.empty_form)

    return render(
        request,
        'account/dashboard_client.html',
        {'section': 'dashboard', 'data': order_formset},
    )


def _dashboard_curator(request):
    return render(
        request,
        'account/dashboard_curator.html',
        {'section': 'dashboard', 'data': 'sample curator data'},
    )


def _dashboard_executor(request):
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
            instance=request.user.profile)
    return render(request,
                  'account/edit.html',
                  {'user_form': user_form,
                   'profile_form': profile_form})
