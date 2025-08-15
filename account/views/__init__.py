import datetime
import os
from io import BytesIO

from urllib.parse import quote
from django.conf import settings
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse, Http404, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Max, Case, When, IntegerField
from django.db.models.functions import Lower
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime

from ..forms import LoginForm, UserEditForm, ProfileEditForm, OrderEditForm, \
OrderEditingForm, EditPlatform, AddGDSFile, MessageForm, EditPaidForm, \
ViewOrderForm, RegistrationForm, AddContractForm, AddContractFileForm
from ..models import Profile, Order, TechnicalProcess, Platform, Substrate, \
Thickness, Diameter, Topic, UserTopic, Message, File, Document, TopicFileModel, \
LoginLog
from ..export_excel import generate_excel_file
from ..utils.email_sender import send_email_with_attachments
from ..utils.generate_messages import add_file_message
from ..utils.unread_message_email_sender import unread_message_email_sender
from ..decorators.restrict import restrict_by_status


def password_recovery(request):
    return render(request, 'account/password_recovery.html')

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


def filter_orders(base_queryset, request):
    # TODO refactor: вытащить request из области видимости функции
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter_by', '')
    # TODO вытащить константы в область видимости файла
    ORDER_STATUS_PRIORITY = [
        'NFW', 'OVK', 'OVC', 'OA', 'CSA', 'ESA', 'SA', 'CGDS', 'EGDS', 'OGDS',
        'POK', 'POC', 'PO', 'MPO', 'SO', 'PS', 'CR', 'EO'
    ]

    if query:
        base_queryset = base_queryset.filter(client__name__icontains=query)

    if filter_by == 'order_number':
        base_queryset = base_queryset.order_by('-order_number')
    elif filter_by == 'created_at':
        base_queryset = base_queryset.order_by('-created_at')
    elif filter_by == 'status':
        whens = [When(order_status=status, then=pos) for pos, status in enumerate(ORDER_STATUS_PRIORITY)]
        base_queryset = base_queryset.annotate(
            status_priority=Case(*whens, output_field=IntegerField())
        ).order_by('status_priority')

    return base_queryset


def client_orders_view(request):
    base_qs = Order.objects.filter(creator_id=request.user.id)
    orders = filter_orders(base_qs, request)
    return render(request, 'account/client/dashboard_client.html', {
        'data': {
            'orders': orders,
        }
    })


def curator_orders_view(request):
    base_qs = Order.objects.all()
    orders = filter_orders(base_qs, request)
    platform = Profile.objects.get(id=request.user.id)
    platform_name = platform.company_name
    return render(request, 'account/dashboard_curator.html', {
        'data': {
            'orders': orders,
            'platform_name': platform_name,
        }
    })


def executor_orders_view(request):
    profile = request.user.profile
    code_company = Platform.objects.get(platform_code=profile.company_name)
    name_platform = Platform.objects.filter(platform_code=code_company).values_list('platform_name', flat=True).first()
    base_qs = Order.objects.filter(platform_code_id=code_company)
    orders = filter_orders(base_qs, request)
    return render(request, 'account/dashboard_executor.html', {
        'data': {
            'orders': orders,
            'name_platform': name_platform,
        }
    })


def registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            user_email = form.cleaned_data['mail']
            subject = 'Регистрация на chip platform'
            body = '''
                <html>
                <body>
                    <h1>Регистрация на chip platform</h1>
                    <p>Сообщаем вам о подаче заявки на регистрацию на платформе chip platform!</p>
                    <p>Просим ознакомиться с приложенными файлами, после заполнения данных отправьте документы по адресу: </br> <strong>ФИЗ.АДРЕС</strong></p>
                    <p>Сканы подписанных документов необходимо отправить на электронную почту: foundry-rf@icvao.ru</p>
                </body>
                </html>
            '''
            sender_email = settings.EMAIL_HOST_USER
            password = settings.EMAIL_HOST_PASSWORD
            file_paths = [
                os.path.join(settings.MEDIA_ROOT, 'uploads/for_send/access_request_form.docx'),
                #os.path.join(settings.MEDIA_ROOT, 'uploads/for_send/Confidentiality_agreement.pdf'),
                os.path.join(settings.MEDIA_ROOT, 'uploads/for_send/Инструкция_пользователя_Платформы_Исполнитель.pdf')
            ]

            send_email_with_attachments(sender_email, user_email, password, subject, body, file_paths)
            
            
            curator_users = User.objects.filter(
                profile__role__name='Куратор',
                profile__deleted_at__isnull=True,
                is_active=True
            ).distinct()

            if not curator_users.exists():
                print('Предупреждение: не найдено активных кураторов для уведомления')

            for curator in curator_users:
                if not curator.email:
                    print(f'Пропуск: у куратора {curator.username} не указан email')
                    continue
                
                curator_subject = 'Новая заявка на регистрацию'
                curator_body = f'''
                    <html>
                    <body>
                        <h1>Новая заявка на регистрацию</h1>
                        <p>Пользователь {form.cleaned_data['name']} ({user_email}) подал заявку на регистрацию.</p>
                        <p>Компания: {form.cleaned_data['company']}</p>
                        <p>Телефон: {form.cleaned_data['number']}</p>
                        <p>Почта: {form.cleaned_data['mail']}</p>
                    </body>
                    </html>
                '''
                try:
                    send_email_with_attachments(
                        sender_email,
                        curator.email,
                        password,
                        curator_subject,
                        curator_body,
                        file_paths=[]
                    )
                    print(f'Уведомление отправлено куратору: {curator.email}')
                except Exception as e:
                    print(f'Ошибка при отправке письма куратору {curator.email}: {e}')

            try:            
                send_email_with_attachments(
                    sender_email,
                    os.getenv('EMAIL_HOST_USER'),
                    password,
                    curator_subject,
                    curator_body,
                    file_paths=[]
                )
                print('Копия письма отправлена на основную почту')
            except Exception as e:
                print(f'Ошибка при отправке копии на основную почту: {e}')
            
            
            messages.success(request, 'Регистрация прошла успешно!')
            return render(request, 'account/registration_done.html')
        else:
            messages.error(request, 'Ошибка в заполнении данных')
    else:
        form = RegistrationForm()

    return render(request, 'account/registration.html', {'form': form})



def download_privacy_file(request):
    """Скачивание файла конфиденциальности"""
    file_path = os.path.join(settings.MEDIA_ROOT, 'uploads/privacy_file/Политика_в_отношении_обработки_персональных_данных.pdf')

    if not os.path.exists(file_path):
        raise Http404('Файл не найден')

    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='Политика_в_отношении_обработки_персональных_данных.pdf')



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
    

def account_expired(request):
    return render(request, 'account/expired.html')


def _dashboard_client(request, message=''):
    profile = request.user.profile
    company_name = profile.company_name
    users_in_company = Profile.objects.filter(company_name=company_name) \
                        .values_list('user', flat=True)
    
    orders = Order.objects.filter(creator__user__in=users_in_company) \
                        .select_related('creator', 'platform_code') \
                        .order_by('-created_at')

    return render(
        request,
        'account/client/dashboard_client.html',
        {
            'section': 'dashboard',
            'data': {
                'platform_name': company_name,
                'orders': orders,
                'profile': profile,
                'current_user_id': request.user.id,
            }
        },
    )


@login_required
def new_order(request):
    profile = request.user.profile.company_name
    
    
    today = datetime.datetime.today().strftime('%Y%m%d')
    today_orders_count = Order.objects.filter(
        order_number__startswith=f'F{today}'
    ).count()

    if today_orders_count > 0:
        new_number = str(today_orders_count + 1).zfill(5)  # +1 и дополняем нулями
    else:
        new_number = '00001'  # первый заказ за день

    order_number = f'F{today}{new_number}'
    
    
    technical_processes = TechnicalProcess.objects.all()

    if request.method == 'POST':
        order_form = OrderEditForm(request.POST, request.FILES)

        if order_form.is_valid():
            order_form.instance.order_number = order_number
            order_form.instance.creator = request.user.profile
            order_form.save(commit=True)
            order_in_progress = Order.objects.latest('created_at')
            order_data = model_to_dict(order_in_progress)
            file_field = order_in_progress.multiplan_dicing_plan_file
            order_data['multiplan_dicing_plan_file'] = file_field.url if file_field else None

            for key, value in list(order_data.items()):
                if not isinstance(value, (str, int, float, bool, type(None))):
                    order_data[key] = str(value)

            # request.session['form_data'] = order_data

            return render(request, 'account/client/new_order_success.html', {'order': order_in_progress})
        else:
            messages.error(request, 'Ошибка в заполнении данных для заказа')
    else:
        # Заполнение данных для заполнения с предыдущего заказа
        # order_form = OrderEditForm(initial=request.session.get('form_data', {}))
        order_form = OrderEditForm()

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
    
def my_documents(request, id):
    nda_documents = Document.objects.filter(document_type='NDA', owner=id)
    consumer_request_documents = Document.objects.filter(document_type='consumer_request', owner=id)
    consumer_form_documents = Document.objects.filter(document_type='consumer_form', owner=id)
    
    profile_id = Profile.objects.get(user_id = id)
    contract_documents = Order.objects.filter(contract_file__isnull=False, creator = profile_id)  # Фильтруем заказы с наличием файла contract_file
    invoice_documents = Order.objects.filter(invoice_file__isnull=False, creator = profile_id)

    context = {
        'nda_documents': nda_documents,
        'consumer_request_documents': consumer_request_documents,
        'consumer_form_documents': consumer_form_documents,
        'contract_documents': contract_documents,
        'invoice_documents': invoice_documents,
    }
    return render(request, 'account/client/my_documents.html', context)
    
def all_documents(request):
    profiles = Profile.objects.filter(role__name__in=['Заказчик', 'Исполнитель'])

    user_documents = {}

    for profile in profiles:
        nda_documents = Document.objects.filter(owner=profile.user, document_type='NDA')
        consumer_request_documents = Document.objects.filter(owner=profile.user, document_type='consumer_request')
        consumer_form_documents = Document.objects.filter(owner=profile.user, document_type='consumer_form')

        contract_documents = Order.objects.filter(creator=profile, contract_file__isnull=False)
        invoice_documents = Order.objects.filter(creator=profile, invoice_file__isnull=False)

        user_documents[profile] = {
            'nda_documents': nda_documents,
            'consumer_request_documents': consumer_request_documents,
            'consumer_form_documents': consumer_form_documents,
            'contract_documents': contract_documents,
            'invoice_documents': invoice_documents,
        }
    return render(request, 'account/all_documents.html', {'user_documents': user_documents})


@login_required
@restrict_by_status()
def changes_in_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order_form = OrderEditForm(request.POST, request.FILES, instance=order)
        if order_form.is_valid():
            order.order_status = 'OVK'
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


@login_required
@restrict_by_status()
def signing_agreement(request, order_id):
    order = Order.objects.get(id=order_id)
    
    if request.method == 'POST':
        form = AddContractForm(request.POST, instance=order)
        if form.is_valid():
            action = None
            if form.cleaned_data.get('contract_is_ready', False):
                order.order_status = 'CSA'
                action = 'confirmed'
            else:
                order.order_status = 'SA'
                action = 'not_confirmed'
            form.save()
            return render(
                request, 
                'account/client/signing_agreement_success.html',
                {'order': order, 'action': action}
            )
    else:
        form = AddContractForm(instance=order)
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)
    
    return render(
        request,
        'account/client/signing_agreement.html',
        {
            'form': form,
            'view_form': view_form,
            'order_items': order_items,
        }
    )

    
@login_required
@restrict_by_status()
def add_gds(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    old_file = order.GDS_file.name
    
    if request.method == 'POST':
        if 'cancel' in request.POST:
            order.order_status = 'OGDS'
            order.save()
            return render(
                request,
                'account/client/add_gds_success.html',
                {'order': order, 'action': 'not_confirmed'}
            )

        form = AddGDSFile(request.POST, request.FILES, instance=order)
        if form.is_valid():
            action = None
            if form.cleaned_data.get('GDS_file', False):
                order.order_status = 'CGDS'
                action = 'confirmed'
                new_file = order.GDS_file.name
                if old_file != new_file:
                    add_file_message(order, 'GDS_file', request.user.profile)
            else:
                order.order_status = 'OGDS'
                action = 'not_confirmed'
            form.save()
            return render(
                request, 
                'account/client/add_gds_success.html',
                {'order': order, 'action': action}
            )
    else:
        form = AddGDSFile(instance=order)
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(
        request,
        'account/client/add_gds.html',
        {
            'form': form,
            'view_form': view_form,
            'order_items': order_items,
        }
    )


@login_required
@restrict_by_status()
def order_paid(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        action = None
        if 'paid_success' in request.POST:
            order.is_paid = True
            order.order_status = 'POK'
            order.order_date = timezone.now()
            action = 'success'
        else:
            pass
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
    
    
@login_required
@restrict_by_status()
def confirmation_receipt(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        action = None
        if 'receipt_success' in request.POST:
            order.is_paid = True
            order.order_status = 'EO'
            action = 'success'
        elif 'receipt_cancel' in request.POST:
            order.is_paid = False
            order.order_status = 'PS'
            action = 'cancelled'
        else:
            order.order_status = 'CR'
            action='unknown'
        order.save()

        return render(
            request,
            'account/client/confirmation_receipt_success.html',
            {'order': order, 'action': action}
        )
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(request, 'account/client/confirmation_receipt.html', {
        'order': order,
        'view_form': view_form,
        'order_items': order_items,
    })


def _dashboard_curator(request, message=''):
    profile = request.user.profile
    orders = Order.objects.all().select_related('creator')
    
    platform = Profile.objects.get(id=request.user.id)
    platform_name = platform.company_name

    return render(
        request,
        'account/dashboard_curator.html',
        {
            'section': 'dashboard',
            'data': {
                'platform_name': platform_name,
                'orders': orders,
                'profile': profile,
            },
        }
    )


@login_required
@restrict_by_status()
def edit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    creator_name = order.creator.user.username

    if request.method == 'POST':
        action = None
        if 'success' in request.POST:
            order.order_status = 'OVC'
            action = 'success'
        elif 'cancelled' in request.POST:
            order.order_status = 'NFW'
            action = 'cancelled'
        order.save()

        return render(
            request, 'account/edit_order_success.html', {'order': order, 'action': action}
            )

    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)
    
    return render(
        request,
        'account/edit_order.html',
        {
            'order': order,
            'view_form': view_form,
            'creator_name': creator_name,
            'order_items': order_items,
            'order_number': order.id,
        }
    )
    
    
@login_required
@restrict_by_status()
def check_signing_curator(request, order_id):
    order = Order.objects.get(id=order_id)
    old_contract = order.contract_file.name or ''
    
    if request.method == 'POST':
        form = AddContractFileForm(request.POST, request.FILES, instance=order)
        action = None
        
        if form.is_valid():
            file_provided = bool(form.cleaned_data.get('contract_file'))
            
            if 'success' in request.POST:
                if file_provided:
                    order.order_status = 'ESA'
                    action = 'success'
                else:
                    order.order_status = 'CSA'
                    action = 'no_file'
            elif 'cancelled' in request.POST:
                if order.contract_file:
                    order.contract_file.delete(save=False)
                    order.contract_file = None
                order.order_status = 'SA'
                action = 'cancelled'
            
            form.save()
            
            new_file = order.contract_file.name or ''
            if action == 'success' and file_provided:
                add_file_message(order, 'contract_file', request.user.profile)
                
            return render(request, 'account/check_signing_success.html', 
                        {'order': order, 'action': action})
    else:
        form = AddContractFileForm(instance=order)
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)
    
    return render(
        request,
        'account/check_signing_curator.html',
        {
            'form': form,
            'view_form': view_form,
            'order_items': order_items,
        }
    )


@login_required
@restrict_by_status()
def view_is_paid(request, order_id):
    order = Order.objects.get(id=order_id)
    old_invoice = order.invoice_file.name or ''
    
    if request.method == 'POST':
        form = EditPaidForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            file_provided = bool(form.cleaned_data.get('invoice_file'))
            action = None
            if 'paid_confirmation' in request.POST:      
                if file_provided:
                    order.is_paid = True
                    order.order_status = 'POC'
                    action = 'success'
                else:
                    order.order_status = 'POK'
                    action = 'no_file'
            elif 'paid_cansel' in request.POST:
                order.is_paid = False
                order.order_status = 'PO'
                action = 'cancelled'
            order.save()
            new_file = order.invoice_file.name or ''
            if old_invoice != new_file and new_file != '' and action == 'success':
                add_file_message(order, 'invoice_file', request.user.profile)
        
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
@restrict_by_status()
def shipping_is_confirm(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        action = None
        if 'success_shipping' in request.POST:
            order.order_status = 'PS'
            action = 'success'
        elif 'cancel_shipping' in request.POST:
            order.order_status = 'MPO'
            action = 'cancelled'
        else:
            order.order_status='SO'
            action='unknown'
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
@restrict_by_status()
def plates_shipped(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        action = None
        if 'success_shipped' in request.POST:
            order.order_status = 'CR'
            action = 'success'
        elif 'cancel_shipped' in request.POST:
            order.order_status = 'SO'
            action = 'cancelled'
        else:
            order.order_status = 'PS'
            action='unknown'
        order.save()

        return render(
            request,
            'account/plates_shipped_success.html',
            {'order': order, 'action': action}
        )

    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)
    
    return render(
        request,
        'account/plates_shipped.html',
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
    orders = Order.objects.filter(platform_code_id=code_company).select_related('creator')
    name_platform = Platform.objects.filter(platform_code=code_company).values_list('platform_name', flat=True).first()
    print(name_platform)

    return render(
        request,
        'account/dashboard_executor.html',
        {
            'section': 'dashboard',
            'data': {
                'orders': orders,
                'name_platform': name_platform,
                'code_company': code_company,
                'profile': profile,
            }
        })


@login_required
@restrict_by_status()
def order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    creator_name = order.creator.user.username

    if request.method == 'POST':
        action = None
        if 'save_changes' in request.POST:
            order.order_status = 'OA'
            action = 'success'
        elif 'cancel_changes' in request.POST:
            order.order_status = 'OVK'
            action = 'cancelled'
        order.save()

        return render(
            request, 'account/order_view_success.html', {'order': order, 'action': action}
        )

    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(
        request,
        'account/order_view.html',
        {
            'order': order,
            'view_form': view_form,
            'creator_name': creator_name,
            'order_items': order_items,
            'order_number': order.id,
            'section': dashboard,
        }
    )


@login_required
def order_view_success(request):
    success_type = request.GET.get('success_type', '')

    if success_type == 'saved':
        message = 'Изменения успешно сохранены!'
    elif success_type == 'canceled':
        message = 'Изменения были отменены.'
    else:
        message = 'Нет информации о действии.'

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
@restrict_by_status()
def check_signing_exec(request, order_id):
    order = Order.objects.get(id=order_id)
    old_contract = order.contract_file.name
    
    if request.method == 'POST':
        action = None
        if 'success' in request.POST:
            order.order_status = 'OGDS'
            action = 'success'
        elif 'cancelled' in request.POST:
            order.order_status = 'CSA'
            action = 'cancelled'
        order.save()
        
        new_file = order.contract_file.name
        if old_contract != new_file and action == 'success':
            add_file_message(order, 'contract_file', request.user.profile)
                    
        return render(
            request,
            'account/check_signing_success.html',
            {'order': order, 'action': action}
        )

    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)
    
    return render(
        request,
        'account/check_signing_exec.html',
        {
            'section': dashboard,
            'view_form': view_form,
            'order_items': order_items,
        }
    )


@login_required
@restrict_by_status()
def check_gds_file_curator(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}
    old_file = order.GDS_file.name
    
    if request.method == 'POST':
        action = None
        if 'success_gds' in request.POST:
            order.order_status = 'EGDS'
            action = 'confirmed'
        elif 'cancel_gds' in request.POST:
            order.order_status = 'OGDS'
            action = 'cancelled'
        else:
            order.order_status = 'CGDS'
            action = ''
        order.save()
        
        new_file = order.GDS_file.name
        if old_file != new_file and 'success_gds' in request.POST:
            add_file_message(order, 'GDS_file', request.user.profile)

        return render(
            request,
            'account/check_gds_file_success.html',
            {'order': order, 'action': action}
        )
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(request, 'account/check_gds_file_curator.html', {
        'section': dashboard,
        'order': order_dict,
        'creator_name': creator_name,
        'view_form': view_form,
        'order_items': order_items,
    }
)
    
    
@login_required
@restrict_by_status()
def check_gds_file_exec(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}
    old_file = order.GDS_file.name
    
    if request.method == 'POST':
        action = None
        if 'success_gds' in request.POST:
            order.order_status = 'PO'
            action = 'confirmed'
        elif 'cancel_gds' in request.POST:
            order.order_status = 'CGDS'
            action = 'cancelled'
        else:
            order.order_status = 'EGDS'
            action = ''
        order.save()
        new_file = order.GDS_file.name
        if old_file != new_file and 'success_gds' in request.POST:
            add_file_message(order, 'GDS_file', request.user.profile)

        return render(
            request,
            'account/check_gds_file_success.html',
            {'order': order, 'action': action}
        )
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(request, 'account/check_gds_file_exec.html', {
        'section': dashboard,
        'order': order,
        'creator_name': creator_name,
        'view_form': view_form,
        'order_items': order_items,
    }
)


@login_required
@restrict_by_status()
def view_is_paid_exec(request, order_id):
    order = Order.objects.get(id=order_id)
    
    if request.method == 'POST':
        action = None
        if 'paid_confirmation' in request.POST:
            order.is_paid = True
            order.order_status = 'MPO'
            action = 'success'
        elif 'paid_cansel' in request.POST:
            order.is_paid = False
            order.order_status = 'POK'
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
@restrict_by_status()
def plates_in_stock(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    mask_name_empty = not order.mask_name or str(order.mask_name).strip() == ''
    action = None

    if request.method == 'POST':
        if 'cancel_confirmation' in request.POST:
            order.order_status = 'POK'
            order.save()
            action = 'cancelled'
            form = None

        elif 'success_confirmation' in request.POST:
            if mask_name_empty:
                form = OrderEditingForm(request.POST, request.FILES, instance=order)
                form.fields['mask_name'].required = True
                if form.is_valid():
                    form.save()
                    order.order_status = 'SO'
                    order.save()
                    action = 'success'
                else:
                    order.order_status = 'MPO'
                    order.save()
                    action = 'missing_mask'
            else:
                form = None
                order.order_status = 'SO'
                order.save()
                action = 'success'
        else:
            form = None
            order.order_status = 'MPO'
            order.save()
            action='unknown'

        if action:
            return render(
                request,
                'account/plates_in_stock_success.html',
                {
                    'order': order,
                    'action': action,
                }
            )
    else:
        form = OrderEditingForm(instance=order) if mask_name_empty else None

    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(
        request,
        'account/plates_in_stock.html',
        {
            'order': order,
            'form': form,
            'view_form': view_form,
            'order_items': order_items,
            'mask_name_empty': mask_name_empty,
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
            return render(request,'account/edit_profile_success.html')
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



def get_diameters_by_platform(platform_id):
    #Хелпер для получения диаметров по платформе
    try:
        diameters = Diameter.objects.filter(platform_id=platform_id)
        print(f'Diameters: {[d.value for d in diameters]}')
        return JsonResponse({
            'diameters': [{'id': d.id, 'value': d.value} for d in diameters]
        })
    except (ValueError, Platform.DoesNotExist):
        return JsonResponse({'error': 'Invalid platform'}, status=400)

def get_all_thicknesses():
    #Хелпер для получения всех толщин
    thicknesses = Thickness.objects.all()
    return JsonResponse({
        'thicknesses': [{'id': t.id, 'value': t.value} for t in thicknesses]
    })

def get_containers_by_format(wafer_deliver_format):
    #Хелпер для получения контейнеров по формату доставки
    if wafer_deliver_format == 'Пластины неразделенные':
        choices = [
            {'id': Order.ContainerForCrystals.СontainerForCrystalls, 'value': 'Тара для пластин'}
        ]
    elif wafer_deliver_format == 'Пластина разделенная на полимерном носителе':
        choices = [
            {'id': Order.ContainerForCrystals.EmFrame, 'value': 'Пяльцы'}
        ]
    elif wafer_deliver_format == 'Кристаллы в таре':
        choices = [
            {'id': Order.ContainerForCrystals.PlasticCells, 'value': 'Пластмассовые ячейки'},
            {'id': Order.ContainerForCrystals.GelPack, 'value': 'Gel-Pak'}
        ]
    else:
        choices = []
    
    return JsonResponse({'container_for_crystals': choices})


def get_technical_processes_by_platform(request):
    # Хелпер для получения доступных техпроцессов по выбранной платформе
    platform_id = request.GET.get('platform_id')
    if platform_id:
        try:
            platform = Platform.objects.get(id=platform_id)
            technical_processes = platform.technicalprocess_set.all()
            technical_processes_data = [
                {'id': tp.id, 'name_process': tp.name_process} for tp in technical_processes
            ]
            return JsonResponse({'technical_processes': technical_processes_data})
        except Platform.DoesNotExist:
            return JsonResponse({'error': 'Platform not found'}, status=404)
    return JsonResponse({'technical_processes': []})


def load_data(request):
    #Использование хелперов на выбор load_data
    platform_id = request.GET.get('platform_id')
    if platform_id:
        try:
            diameters_qs = Diameter.objects.filter(platform_id=platform_id)
            diameters = [{'id': d.id, 'value': d.value} for d in diameters_qs]
        except (ValueError, Platform.DoesNotExist):
            diameters = []
        try:
            platform = Platform.objects.get(id=platform_id)
            tech_qs = platform.technicalprocess_set.all()
            technical_processes = [{'id': tp.id, 'name_process': tp.name_process} for tp in tech_qs]
        except Platform.DoesNotExist:
            technical_processes = []
        return JsonResponse({
            'diameters': diameters,
            'technical_processes': technical_processes
        })
        
    #TODO В будущем разобраться с двойным вызовом

    substrate_type = request.GET.get('substrate_type')
    if substrate_type:
        return get_all_thicknesses()

    wafer_deliver_format = request.GET.get('wafer_deliver_format')
    if wafer_deliver_format:
        return get_containers_by_format(wafer_deliver_format)

    return JsonResponse({'error': 'Invalid request'}, status=400)



def new_order_success_view(request):
    return render(request, 'new_order_success.html')


def download_excel_file_from_order_id(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponse('Ошибка: заказ не найден.', status=404)

    wb = generate_excel_file(request, order_id=order_id)

    if wb:
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f'Детали_заказа_{order_id}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{quote(filename)}"; filename*=UTF-8\'\'{quote(filename)}'
        return response
    else:
        return HttpResponse('Ошибка при создании файла.', status=400)


def help_files(request):
    files = TopicFileModel.objects.all()
    return render(request, 'account/help_files.html', {
        'files': files,
        'section': 'help_files',
    })


def feedback(request):
    files = TopicFileModel.objects.all()
    user = request.user
    profile = user.profile
    private_topics = Topic.objects.filter(
        is_private=True,
        usertopic__user=profile
    ).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')
    
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
        'private_topics': private_topics,
        'sub_section': tab,
        'files': files,
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

        message_text = request.POST.get('text', '').strip()

        if message_text or files:
            message = Message(topic=topic, user=profile, text=message_text if message_text else '')
            message.save()
            unread_message_email_sender(message.id)

            for file in files:
                File.objects.create(message=message, file=file)

            if topic.is_private:
                topic.name = f'Чат по заказу {topic.related_order.order_number} | {localtime().strftime('%H:%M:%S')}'
                topic.save(update_fields=['name'])

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


# def create_general_topic(request):
#     if request.method == 'POST':
#         topic_name = request.POST.get('topic_name')
#         if topic_name:  
#             topic = Topic.objects.create(
#                 name=topic_name,
#                 is_private=False
#             )
#             return redirect('topic_detail', topic_id=topic.id)
#         else:
#             messages.error(request, 'Название комнаты не может быть пустым.')
#     return redirect('feedback')


def upload_files(request):
    if request.method == 'POST' and request.FILES:
        files = request.FILES.getlist('file')
        file_urls = []

        for file in files:
            file_instance = File.objects.create(file=file)
            file_urls.append(file_instance.file.url)

        return JsonResponse({'message': 'Файлы успешно загружены!', 'file_urls': file_urls})

    return JsonResponse({'error': 'Ошибка при загрузке файлов.'})


def check_the_order(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(
        request,
        'account/check_the_order.html',
        {
            'order': order_dict,
            'creator_name': creator_name,
            'view_form': view_form,
            'order_items': order_items,
        }
    )
    
def set_theme(request):
    theme = request.POST.get('theme', 'light')
    
    if theme in ['light', 'dark']:
        request.session['theme'] = theme
        return JsonResponse({'status': 'success', 'theme': theme})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def login_log_view(request):
    logs = LoginLog.objects.all().order_by('-login_time')
    return render(request, 'account/login_logs.html', {'logs': logs})
