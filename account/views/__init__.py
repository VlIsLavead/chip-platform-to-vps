import datetime
import os
from io import BytesIO

from django.core.mail import send_mail
from urllib.parse import quote
from django.conf import settings
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse, Http404, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Max
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
Thickness, Diameter, Topic, UserTopic, Message, File, Document, TopicFileModel
from ..export_excel import generate_excel_file
from ..utils.email_sender import send_email_with_attachments


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


def registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            user_email = form.cleaned_data['mail']
            subject = "Регистрация на chip platform"
            body = """
                <html>
                <body>
                    <h1>Регистрация на chip platform</h1>
                    <p>Вы подали заявку на регистрацию на платформе chip platform.</p>
                    <p>Ознакомьтесь с приложенными файлами, заполните данные и отправьте по адресу: <strong>ФИЗ.АДРЕС</strong></p>
                </body>
                </html>
            """
            sender_email = settings.EMAIL_HOST_USER
            password = settings.EMAIL_HOST_PASSWORD
            file_paths = [
                os.path.join(settings.MEDIA_ROOT, 'uploads/for_send/file_one.txt'),
                os.path.join(settings.MEDIA_ROOT, 'uploads/for_send/file_two.txt')
            ]

            send_email_with_attachments(sender_email, user_email, password, subject, body, file_paths)
            messages.success(request, 'Регистрация прошла успешно!')
            return render(request, 'account/registration_done.html')
        else:
            messages.error(request, 'Ошибка в заполнении данных')
    else:
        form = RegistrationForm()

    return render(request, 'account/registration.html', {'form': form})



def download_privacy_file(request):
    """Скачивание файла конфиденциальности"""
    file_path = os.path.join(settings.MEDIA_ROOT, 'uploads/privacy_file/privacy_file.txt')

    if not os.path.exists(file_path):
        raise Http404("Файл не найден")

    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename="privacy_file.txt")



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
    
    
def my_documents(request):
    nda_documents = Document.objects.filter(document_type='NDA')
    consumer_request_documents = Document.objects.filter(document_type='consumer_request')
    consumer_form_documents = Document.objects.filter(document_type='consumer_form')
    
    contract_documents = Order.objects.filter(contract_file__isnull=False)  # Фильтруем заказы с наличием файла contract_file
    invoice_documents = Order.objects.filter(invoice_file__isnull=False)

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


def signing_agreement(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}
    
    if request.method == 'POST':
        form = AddContractForm(request.POST, instance=order)
        if form.is_valid():
            order.order_status = "CSA"
            form.save()
            return render(request, 'account/client/signing_agreement_success.html', )
    else:
        form = AddContractForm(instance=order)
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)
    
    return render(
        request,
        'account/client/signing_agreement.html',
        {
            'form': form,
            'order': order_dict,
            'creator_name': creator_name,
            'view_form': view_form,
            'order_items': order_items,
        }
    )

    

def add_gds(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}

    if request.method == 'POST':
        form = AddGDSFile(request.POST, request.FILES, instance=order)
        if form.is_valid():
            order.order_status = "CGDS"
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
            order.order_date = timezone.now()
            action = 'success'
        elif 'paid_cansel' in request.POST:
            order.is_paid = False
            order.order_status = "PO"
            order.order_date = None
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
    
    
@login_required
def confirmation_receipt(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        action = None
        if 'receipt_success' in request.POST:
            order.is_paid = True
            order.order_status = "EO"
            action = 'success'
        elif 'receipt_cancel' in request.POST:
            order.is_paid = False
            order.order_status = "PS"
            action = 'cancelled'
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

    if request.method == 'POST':
        action = None
        if 'success' in request.POST:
            order.order_status = "OVC"
            action = 'success'
        elif 'cancelled' in request.POST:
            order.order_status = "NFW"
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
    
    
def check_signing_curator(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}
    
    if request.method == 'POST':
        form = AddContractFileForm(request.POST,  request.FILES, instance=order)
        action = None
        if 'success' in request.POST:
            order.order_status = "ESA"
            action = 'success'
        elif 'cancel' in request.POST:
            order.order_status = "SA"
            action = 'cancelled'
        if form.is_valid():
            form.save()
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
            'order': order_dict,
            'creator_name': creator_name,
            'view_form': view_form,
            'order_items': order_items,
        }
    )


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
            order.order_status = "PS"
            action = 'success'
        elif 'cancel_shipping' in request.POST:
            order.order_status = "MPO"
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
def plates_shipped(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        action = None
        if 'success_shipped' in request.POST:
            order.order_status = "CR"
            action = 'success'
        elif 'cancel_shipped' in request.POST:
            order.order_status = "SO"
            action = 'cancelled'
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


def check_signing_exec(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}

    if request.method == "POST":
        action = None
        if 'success' in request.POST:
            order.order_status = "OGDS"
            action = 'success'
        elif 'cancel' in request.POST:
            order.order_status = "CSA"
            action = 'cancelled'
        order.save()      
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
            'order': order_dict,
            'creator_name': creator_name,
            'view_form': view_form,
            'order_items': order_items,
        }
    )

@login_required
def check_gds_file_curator(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}

    if request.method == 'POST':
        action = None
        if 'success_gds' in request.POST:
            order.order_status = "EGDS"
            action = 'confirmed'
        elif 'cancel_gds' in request.POST:
            order.order_status = "OGDS"
            action = 'cancelled'
        order.save()

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
def check_gds_file_exec(request, order_id):
    order = Order.objects.get(id=order_id)
    creator_name = order.creator.user.username
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}

    if request.method == 'POST':
        action = None
        if 'success_gds' in request.POST:
            order.order_status = "PO"
            action = 'confirmed'
        elif 'cancel_gds' in request.POST:
            order.order_status = "CGDS"
            action = 'cancelled'
        order.save()

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
    order = get_object_or_404(Order, id=order_id)
    order_dict = {key: value for key, value in order.__dict__.items() if not key.startswith('_')}
    mask_name_empty = not order.mask_name or str(order.mask_name).strip() == ''
    
    if request.method == 'POST':
        if mask_name_empty:
            form = OrderEditingForm(request.POST, request.FILES, instance=order)
            if form.is_valid():
                form.save()
                mask_name_empty = False
        else:
            form = None

        action = None
        if 'success_confirmation' in request.POST:
            order.order_status = "SO"
            action = 'success'
        elif 'cancel_confirmation' in request.POST:
            order.order_status = "POK"
            action = 'cancelled'
        
        order.save()
        
        if action:
            return render(
                request,
                'account/plates_in_stock_success.html',
                {'order': order, 'action': action}
            )
    else:
        form = OrderEditingForm(instance=order) if not order.mask_name else None
        
    view_form = ViewOrderForm(instance=order)
    order_items = view_form.get_order_data(order)

    return render(
        request,
        'account/plates_in_stock.html',
        {
            'order': order,
            'form': form,
            'order_dict': order_dict,
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

        message_text = request.POST.get('text', '').strip()  # Получаем текст из формы

        if message_text or files:  # Разрешаем отправку только если есть текст или файлы
            message = Message(topic=topic, user=profile, text=message_text if message_text else "")
            message.save()

            for file in files:
                File.objects.create(message=message, file=file)

            if topic.is_private:
                topic.name = f'Чат по заказу {topic.related_order.order_number} | {localtime().strftime("%H:%M:%S")}'
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
