from django.urls import path, include
from . import views


# TODO normalize all URLs, use dash instead of underscore, remove trailing slashes(?)
urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('registration/', views.registration, name='registration'),
    path('registration/download/', views.download_privacy_file, name='download_privacy_file'),
    path('logout/', views.user_logout, name='logout'),
    path('', include('django.contrib.auth.urls')),
    path('', views.dashboard, name='dashboard'),
    # TODO unify search urls, they shouldn't lead to different endpoints
    path('search/', views.generic_search_clients, name='generic_search_clients'),
    path('search_c/', views.generic_search_curator, name='generic_search_curator'),
    path('search_e/', views.generic_search_executor, name='generic_search_executor'),
    path('edit/', views.edit, name='edit'),
    path('new_order/', views.new_order, name='new_order'),
    path('technical_materials/', views.technical_materials, name='technical_materials'),
    path('new_order_success/', views.new_order_success_view, name='new_order_success'),
    path('download_excel/', views.download_excel_file_from_session, name='download_excel_from_session'),
    path('download_excel/<int:order_id>/', views.download_excel_file_from_order_id, name='download_excel_from_order_id'),
    path('edit_order/<int:order_id>', views.edit_order, name='edit_order'),
    path('edit_platform', views.edit_platform, name='edit_platform'),
    path('edit_platform-success', views.edit_platform_success, name='edit_platform_success'),
    path('changes_in_order/<int:order_id>', views.changes_in_order, name='changes_in_order'),
    path('order_view/<int:order_id>', views.order_view, name='order_view'),
    path('order_view/success/', views.order_view_success, name='order_view_success'),
    path('signing_agreement/<int:order_id>', views.signing_agreement, name='signing_agreement'),
    path('check_signing_curator/<int:order_id>', views.check_signing_curator, name='check_signing_curator'),
    path('check_signing_exec/<int:order_id>', views.check_signing_exec, name='check_signing_exec'),
    path('add_gds/<int:order_id>/', views.add_gds, name='add_gds'),
    path('check_gds_file_curator/<int:order_id>/', views.check_gds_file_curator, name='check_gds_file_curator'),
    path('check_gds_file_exec/<int:order_id>/', views.check_gds_file_exec, name='check_gds_file_exec'),
    path('order_paid/<int:order_id>/', views.order_paid, name='is_paid'),
    path('view_is_paid/<int:order_id>/', views.view_is_paid, name='view_is_paid'),
    path('view_is_paid_exec/<int:order_id>/', views.view_is_paid_exec, name='view_is_paid_exec'),
    path('plates_in_stock/<int:order_id>/', views.plates_in_stock, name='plates_in_stock'),
    path('shipping_is_confirm/<int:order_id>/', views.shipping_is_confirm, name='shipping_is_confirm'),
    path('plates_shipped/<int:order_id>/', views.plates_shipped, name='plates_shipped'),
    path('confirmation_receipt/<int:order_id>/', views.confirmation_receipt, name='confirmation_receipt'),
    path('feedback/', views.feedback, name='feedback'),
    path('topic/<int:topic_id>/', views.topic_detail, name='topic_detail'),
    path('create_or_open_chat/<int:order_id>/', views.create_or_open_chat, name='create_or_open_chat'),
    path('chat/create_general/', views.create_general_topic, name='create_general_topic'),
    path('upload/', views.upload_files, name='upload_files'),

    path('load-data/', views.load_data, name='load_data')  # AJAX
]
