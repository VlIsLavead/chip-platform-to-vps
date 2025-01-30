import datetime
from io import BytesIO

from urllib.parse import quote
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Value
from django.db.models.functions import Lower
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils.timezone import localtime

from ..forms import LoginForm, UserEditForm, ProfileEditForm, OrderEditForm, OrderEditingForm, EditPlatform, AddGDSFile, MessageForm, EditPaidForm, ViewOrderForm
from ..models import Profile, Order, TechnicalProcess, Platform, Substrate, Thickness, Diameter, Topic, UserTopic, Message, File
from ..export_excel import generate_excel_file


def filter_orders(orders, query):
    filtered_orders = orders.filter(
        Q(order_number__icontains=query) |
        Q(id__icontains=query) |
        Q(platform_code__platform_code__icontains=query) |
        Q(order_date__icontains=query) |
        Q(deadline_date__icontains=query) |
        Q(contract_file__icontains=query) |
        Q(invoice_file__icontains=query) |
        Q(GDS_file__icontains=query)
    )

    additional_orders = []
    for order in orders:
        if query.lower() in order.get_order_type_display().lower() or query.lower() in order.get_order_status_display().lower():
            additional_orders.append(order)

    return (filtered_orders | orders.filter(id__in=[o.id for o in additional_orders])).distinct()



def generic_search_clients(request):
    query = request.GET.get('q')
    orders = Order.objects.filter(creator_id=request.user.id)
    filtered_orders = filter_orders(orders, query)

    data = {
        'orders': filtered_orders,
        'profile': {'company': 'Рога и Копыта'},
    }
    return render(request, 'account/client/dashboard_client.html', {'data': data})



def generic_search_curator(request):
    query = request.GET.get('q')
    orders = Order.objects.all()
    filtered_orders = filter_orders(orders, query)

    data = {
        'orders': filtered_orders,
        'profile': {'company': 'рога и копыта'},
    }
    return render(request, 'account/dashboard_curator.html', {'data': data})



def generic_search_executor(request):
    query = request.GET.get('q')
    user_p = request.user.profile
    code_company = Platform.objects.get(platform_code=user_p.company_name)
    orders = Order.objects.filter(platform_code_id=code_company)
    filtered_orders = filter_orders(orders, query)

    data = {
        'profile': user_p,
        'code_company': code_company,
        'orders': filtered_orders,
    }
    return render(request, 'account/dashboard_executor.html', {'data': data})



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
    profile = request.user.profile.company_name
    last_order = Order.objects.latest("created_at")
    date_last_order, number_last_order = last_order.order_number[1:9], int(last_order.order_number[9:])
    if date_last_order == datetime.datetime.today().strftime("%Y%m%d"):
        new_number = str(number_last_order + 1).zfill(5)
    else:
        new_number = '00001'
    order_number = str('F' + datetime.datetime.today().strftime("%Y%m%d") + new_number)
    technical_processes = TechnicalProcess.objects.all()

    if request.method == 'POST':
        order_form = OrderEditForm(request.POST, request.FILES)

        if order_form.is_valid():
            order_form.instance.order_number = order_number
            order_form.instance.creator = request.user.profile
            order_form.save(commit=True)
            order_in_progress = Order.objects.latest("created_at")
            order_data = model_to_dict(order_in_progress)
            file_field = order_in_progress.multiplan_dicing_plan_file
            order_data['multiplan_dicing_plan_file'] = file_field.url if file_field else None

            for key, value in list(order_data.items()):
                if not isinstance(value, (str, int, float, bool, type(None))):
                    order_data[key] = str(value)

            request.session['form_data'] = order_data

            return render(request, 'account/client/new_order_success.html')
        else:
            messages.error(request, 'Ошибка в заполнении данных для заказа')
    else:
        order_form = OrderEditForm(initial=request.session.get('form_data', {}))

    return render(
        request,
        'account/client/new_order.html',
        {
            'profile': profile,
            'order_form': order_form,
            'order_number': order_number,
            'technical_processes': technical_processes,
        }
    )


def technical_materials(request):
    techprocess = TechnicalProcess.objects.values('name_process').distinct()
    selected_process_name = request.GET.get('technical_process')
    selected_process = None

    if selected_process_name:
        selected_process = TechnicalProcess.objects.filter(name_process=selected_process_name).first()

    return render(request, 'account/client/technical_materials.html', {
        'techprocess': techprocess,
        'selected_process': selected_process,
        'section': 'technical_materials',
    })


def changes_in_order(request, order_id):
    order = Order.objects.get(id=order_id)
    if request.method == 'POST':
        order_form = OrderEditForm(request.POST, request.FILES, instance=order)
        if order_form.is_valid():
            order.order_status = "OVK"
            order_form.save()
            return render(request, 'account/client/changes_in_order_success.html',
                          {'order_form': order_form,
                          'order_id': order_id})
        else:
            messages.error(request, 'Ошибка в заполнении данных для заказа')
    else:
        order_form = OrderEditForm(instance=order)
    return render(request, 'account/client/changes_in_order.html', {
        'order': order,
        'order_form': order_form,
        'order_id': order_id,
    })


def add_gds(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}

    if request.method == 'POST':
        form = AddGDSFile(request.POST, request.FILES, instance=order)
        if form.is_valid():
            order.order_status = "OGDS"
            form.save()
            return render(request, 'account/client/add_gds_success.html', )
    else:
        form = AddGDSFile(instance=order)
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(
        request,
        'account/client/add_gds.html',
        {
            'form': form,
            'order': order_dict,
            'creator_name': creator_name,
            'view_form': view_form,
            'order_items': order_items,
        }
    )


@login_required
def order_paid(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        action = None
        if 'paid_success' in request.POST:
            order.is_paid = True
            order.order_status = "POK"
            action = 'success'
        elif 'paid_cansel' in request.POST:
            order.is_paid = False
            order.order_status = "PO"
            action = 'cancelled'
        order.save()

        return render(
            request,
            'account/client/order_paid_success.html',
            {'order': order, 'action': action}
        )
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(request, 'account/client/order_paid.html', {
        'order': order,
        'view_form': view_form,
        'order_items': order_items,
    })


def _dashboard_curator(request, message=''):
    orders = Order.objects.all()

    return render(
        request,
        'account/dashboard_curator.html',
        {
            'section': 'dashboard',
            'data': {
                'orders': orders,
                'profile': {'company': 'рога и копыта'},
            },
        }
    )


@login_required
def edit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}

    if request.method == 'POST':
        form = OrderEditingForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            action = None
            if 'success' in request.POST:
                order.order_status = "OVC"
                action = 'success'
            elif 'canselled' in request.POST:
                order.order_status = "NFW"
                action = 'cancelled'
            order.save()
            return render(request, 'account/edit_order_success.html', {'order': order, 'action': action})
    else:
        form = OrderEditingForm(instance=order)
        
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)


    return render(request, 'account/edit_order.html', {
        'view_form': view_form,
        'order_items': order_items,
        'form': form,
        'order_number': order.id,
        'creator_name': creator_name,
        'order': order_dict,
    })


@login_required
def view_is_paid(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        form = EditPaidForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            action = None
            if 'paid_confirmation' in request.POST:
                order.is_paid = True
                order.order_status = "POC"
                action = 'success'
            elif 'paid_cansel' in request.POST:
                order.is_paid = False
                order.order_status = "PO"
                action = 'cancelled'
            order.save()
            return render(
                request,
                'account/view_is_paid_success.html',
                {'order': order, 'action': action}
            )
    else:
        form = EditPaidForm(instance=order)
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)
            
    return render(
        request,
        'account/view_is_paid.html',
        {
            'view_form': view_form,
            'order_items': order_items,
            'form': form,
            'order': order,
        }
    )


@login_required
def shipping_is_confirm(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        action = None
        if 'success_shipping' in request.POST:
            order.order_status = "EO"
            action = 'success'
        elif 'cansel_shipping' in request.POST:
            order.order_status = "SO"
            action = 'cancelled'
        order.save()

        return render(
            request,
            'account/shipping_is_confirm_success.html',
            {'order': order, 'action': action}
        )

    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)
    
    return render(
        request,
        'account/shipping_is_confirm.html',
        {
            'order': order,
            'view_form': view_form,
            'order_items': order_items,
        }
    )


@login_required
def _dashboard_executor(request, message=''):
    profile = request.user.profile
    code_company = Platform.objects.get(platform_code=profile.company_name)
    orders = Order.objects.filter(platform_code_id=code_company)
    name_platform = Platform.objects.filter(platform_code=code_company).values_list('platform_name', flat=True).first()

    return render(
        request,
        'account/dashboard_executor.html',
        {
            'section': 'dashboard',
            'data': {
                'orders': orders,
                'name_platform': name_platform,
                'code_company': code_company,
                'profile': {'company': 'рога и копыта'},
            }
        })


@login_required
def order_view(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}
    print(creator_name)

    if request.method == "POST":
        if 'save_changes' in request.POST:
            order.order_status = "OA"
            order.save()
            return redirect(reverse('order_view_success') + '?success_type=saved')
        elif 'cancel_changes' in request.POST:
            pass
        return redirect(reverse('order_view_success') + '?success_type=canceled')

    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)
    
    return render(
        request,
        'account/order_view.html',
        {
            'section': dashboard,
            'order': order_dict,
            'creator_name': creator_name,
            'view_form': view_form,
            'order_items': order_items,
        }
    )


@login_required
def order_view_success(request):
    success_type = request.GET.get('success_type', '')

    if success_type == 'saved':
        message = "Изменения успешно сохранены!"
    elif success_type == 'canceled':
        message = "Изменения были отменены."
    else:
        message = "Нет информации о действии."

    return render(
        request,
        'account/order_view_success.html',
        {
            'message': message
        }
    )


@login_required
def edit_platform(request):
    if request.method == 'POST':
        editing_form = EditPlatform(request.POST)
        if editing_form.is_valid():
            editing_form.save()
            return redirect('edit_platform_success')
    else:
        editing_form = EditPlatform()

    return render(request,
                  'account/edit_platform.html',
                  {'editing_form': editing_form})


@login_required
def edit_platform_success(request):
    return render(request, 'account/edit_platform_success.html')


@login_required
def check_gds_file(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username

    if request.method == 'POST':
        action = None
        if 'success_gds' in request.POST:
            order.order_status = "PO"
            action = 'confirmed'
        elif 'cansel_gds' in request.POST:
            order.order_status = "OA"
            action = 'cancelled'
        order.save()

        return render(
            request,
            'account/check_gds_file_success.html',
            {'order': order, 'action': action}
        )

    return render(request, 'account/check_gds_file.html', {
        'data': {
            'order': order,
            'creator_name': creator_name,
        }
    }
                  )


@login_required
def view_is_paid_exec(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        action = None
        if 'paid_confirmation' in request.POST:
            order.is_paid = True
            order.order_status = "MPO"
            action = 'success'
        elif 'paid_cansel' in request.POST:
            order.is_paid = False
            order.order_status = "POK"
            action = 'cancelled'
        order.save()

        return render(
            request,
            'account/view_is_paid_exec_success.html',
            {'order': order, 'action': action}
        )
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(
        request,
        'account/view_is_paid_exec.html',
        {
            'view_form': view_form,
            'order_items': order_items,
            'order': order,
        }
    )


@login_required
def plates_in_stock(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        action = None
        if 'success_confirmation' in request.POST:
            order.is_paid = True
            order.order_status = "SO"
            action = 'success'
        elif 'cansel_confirmation' in request.POST:
            order.is_paid = False
            order.order_status = "MPO"
            action = 'cancelled'
        order.save()

        return render(
            request,
            'account/plates_in_stock_success.html',
            {'order': order, 'action': action}
        )
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(
        request,
        'account/plates_in_stock.html',
        {
            'order': order,
            'view_form': view_form,
            'order_items': order_items,
        }
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


def load_data(request):
    substrate_type = request.GET.get('substrate_type')

    if substrate_type not in [Substrate.STANDARD, Substrate.NON_STANDARD]:
        return JsonResponse({'error': 'Invalid substrate type'}, status=400)

    thicknesses = Thickness.objects.filter(type=substrate_type)
    thickness_data = [{'id': t.id, 'value': t.value} for t in thicknesses]

    diameters = Diameter.objects.filter(type=substrate_type)
    diameter_data = [{'id': d.id, 'value': d.value} for d in diameters]

    wafer_deliver_format = request.GET.get('wafer_deliver_format')

    if wafer_deliver_format == 'Пластины неразделенные':
        container_for_crystals_choices = [
            {'id': Order.ContainerForCrystals.СontainerForCrystalls, 'value': 'Тара для пластин'}
        ]
    elif wafer_deliver_format == 'Пластина разделенная на полимерном носителе':
        container_for_crystals_choices = [
            {'id': Order.ContainerForCrystals.PlasticCells, 'value': 'Пластмассовые ячейки'}
        ]
    elif wafer_deliver_format == 'Кристаллы в таре':
        container_for_crystals_choices = [
            {'id': Order.ContainerForCrystals.GelPack, 'value': 'Gel-Pak'}
        ]
    else:
        container_for_crystals_choices = []

    return JsonResponse({
        'thicknesses': thickness_data,
        'diameters': diameter_data,
        'container_for_crystals': container_for_crystals_choices
    })



def new_order_success_view(request):
    return render(request, 'new_order_success.html')


def download_excel_file_from_session(request):
    form_data = request.session.get('form_data', {})
    order_id = form_data.get('id')
    if not order_id:
        print('Ошибка: не найден order_id в form_data сессии.')
        return HttpResponse("Ошибка: не найден order_id в form_data сессии.", status=400)

    session_data = dict(request.session)
    try:
        wb = generate_excel_file(request, session_data=session_data, order_id=order_id)
    except Exception as e:
        print('Ошибка генерации Excel:', e)
        return HttpResponse("Ошибка при создании файла.", status=500)

    if wb:
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"Детали_заказа_{order_id}.xlsx"
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
        return response
    else:
        return HttpResponse("Ошибка при создании файла.", status=400)


def download_excel_file_from_order_id(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponse("Ошибка: заказ не найден.", status=404)

    session_data = request.session

    wb = generate_excel_file(request, session_data=session_data, order_id=order_id)

    if wb:
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f"Детали_заказа_{order_id}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
        return response
    else:
        return HttpResponse("Ошибка при создании файла.", status=400)


def feedback(request):
    user = request.user
    profile = user.profile
    general_topics = Topic.objects.filter(is_private=False)
    private_topics = Topic.objects.filter(
        is_private=True,
        usertopic__user=profile
    )
    
    for topic in general_topics:
        last_read_message = UserTopic.objects.filter(user=profile, topic=topic).first()
        if last_read_message and last_read_message.last_read_message:
            topic.unread_count = Message.objects.filter(
                topic=topic,
                id__gt=last_read_message.last_read_message.id
            ).count()
        else:
            topic.unread_count = 0
        
        last_message = Message.objects.filter(topic=topic).order_by('-created_at').first()
        topic.last_message_time = last_message.created_at if last_message else None
    
    for topic in private_topics:    
        last_read_message = UserTopic.objects.filter(user=profile, topic=topic).first()
        if last_read_message and last_read_message.last_read_message:
            topic.unread_count = Message.objects.filter(
                topic=topic,
                id__gt=last_read_message.last_read_message.id
            ).count()
        else:
            topic.unread_count = 0 
        
        last_message = Message.objects.filter(topic=topic).order_by('-created_at').first()
        topic.last_message_time = last_message.created_at if last_message else None
    
    tab = request.GET.get('tab', 'general')

    return render(request, 'account/feedback.html', {
        'general_topics': general_topics,
        'private_topics': private_topics,
        'sub_section': tab,
        'section': 'feedback',
    })


def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    messages = Message.objects.filter(topic=topic)

    profile = request.user.profile
    user_topic, created = UserTopic.objects.get_or_create(user=profile, topic=topic)

    last_message = Message.objects.filter(topic=topic).order_by('-id').first()
    if last_message:
        user_topic.last_read_message = last_message
        user_topic.save()

    if request.method == 'POST':
        message_form = MessageForm(request.POST)
        files = request.FILES.getlist('file')

        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.topic = topic
            message.user = profile
            message.save()

            if topic.is_private:
                topic.name = f'Чат {topic.related_order.order_number} | {localtime().strftime("%H:%M:%S")}'
                topic.save(update_fields=['name'])

            for file in files:
                File.objects.create(message=message, file=file)

            return redirect('topic_detail', topic_id=topic.id)
    else:
        message_form = MessageForm()

    return render(request, 'account/feedback/topic_detail.html', {
        'topic': topic,
        'messages': messages,
        'message_form': message_form,
    })

def create_or_open_chat(request, order_id):
    order = Order.objects.get(id=order_id)

    topic, created = Topic.objects.get_or_create(
        related_order=order,
        defaults={
            'name': f'Чат {order.order_number} | ',
            'is_private': True
        }
    )

    if request.user.is_authenticated:
        UserTopic.objects.get_or_create(user=request.user.profile, topic=topic)

    curator = Profile.objects.filter(role__name='Куратор', company_name=order.platform_code).first()
    if curator:
        UserTopic.objects.get_or_create(user=curator, topic=topic)

    executor = Profile.objects.filter(role__name='Исполнитель').first()
    if executor:
        UserTopic.objects.get_or_create(user=executor, topic=topic)

    return redirect('topic_detail', topic_id=topic.id)


def create_general_topic(request):
    if request.method == 'POST':
        topic_name = request.POST.get('topic_name')
        if topic_name:  
            topic = Topic.objects.create(
                name=topic_name,
                is_private=False
            )
            return redirect('topic_detail', topic_id=topic.id)
        else:
            messages.error(request, 'Название комнаты не может быть пустым.')
    return redirect('feedback')


def upload_files(request):
    if request.method == 'POST' and request.FILES:
        files = request.FILES.getlist('file')
        file_urls = []

        for file in files:
            file_instance = File.objects.create(file=file)
            file_urls.append(file_instance.file.url)

        return JsonResponse({'message': 'Файлы успешно загружены!', 'file_urls': file_urls})

    return JsonResponse({'error': 'Ошибка при загрузке файлов.'})
