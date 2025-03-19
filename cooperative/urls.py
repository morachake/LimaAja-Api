from django.urls import path
from . import views

urlpatterns = [
    path('', views.cooperative_index, name='cooperative_index'),
    path('login/', views.cooperative_login, name='cooperative_login'),
    path('register/', views.cooperative_register, name='cooperative_register'),
    path('verification/', views.cooperative_verification, name='cooperative_verification'),
    path('document-upload/', views.document_upload, name='document_upload'),
    path('awaiting-verification/', views.awaiting_verification, name='awaiting_verification'),
    path('dashboard/', views.cooperative_dashboard, name='cooperative_dashboard'),
    path('produce/<int:produce_type_id>/', views.produce_detail, name='produce_detail'),
    path('add-produce/', views.add_produce, name='add_produce'),
    path('update-produce/<int:produce_id>/', views.update_produce, name='update_produce'),
    path('delete-produce/<int:produce_id>/', views.delete_produce, name='delete_produce'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('logout/', views.logout_view, name='logout'),
    path('check-approval-status/', views.check_approval_status, name='check_approval_status'),
]

