from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

# from .views import new_order

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),


    path('', include('django.contrib.auth.urls')),
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='edit'),
    path('new_order/', views.new_order, name='new_order'),
    path('technical_materials/', views.technical_materials, name='technical_materials'),
    path('new_order_success/', views.new_order_success_view, name='new_order_success'),
    path('download_excel/', views.download_excel_file, name='download_excel'), 
    path('edit_order/<int:order_id>', views.edit_order, name='edit_order'),
    path('edit-platform', views.edit_platform, name='edit_platform'),
    path('edit-platform-success', views.edit_platform_success, name='edit_platform_success'),
    
  
  path('load-data/', views.load_data, name='load_data')   # AJAX
]

