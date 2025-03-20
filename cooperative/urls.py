from django.urls import path
from . import views

urlpatterns = [
    path('', views.cooperative_index, name='cooperative_index'),
    path('login/', views.cooperative_login, name='cooperative_login'),
    path('register/', views.cooperative_register, name='cooperative_register'),
    path('verification/', views.cooperative_verification, name='cooperative_verification'),
    path('awaiting-verification/', views.awaiting_verification, name='awaiting_verification'),
    path('dashboard/', views.cooperative_dashboard, name='cooperative_dashboard'),
    path('document-upload/', views.document_upload, name='document_upload'),
    path('logout/', views.logout_view, name='logout'),
    path('check-approval-status/', views.check_approval_status, name='check_approval_status'),
    path('dashboard/produce/<int:produce_type_id>/', views.produce_detail, name='produce_detail'),
    path('dashboard/add-produce/', views.add_produce, name='add_produce'),
    path('dashboard/update-produce/<int:produce_id>/', views.update_produce, name='update_produce'),
    path('dashboard/delete-produce/<int:produce_id>/', views.delete_produce, name='delete_produce'),
    path('dashboard/order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('dashboard/order/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('dashboard/request-money/', views.request_money, name='request_money'),
    
    
    path('dashboard/add-bank-account/', views.add_bank_account, name='add_bank_account'),
    path('dashboard/delete-bank-account/<int:account_id>/', views.delete_bank_account, name='delete_bank_account'),
    path('dashboard/set-primary-bank-account/<int:account_id>/', views.set_primary_bank_account, name='set_primary_bank_account'),
  
    
    # API endpoints
    path('api/farmers/', views.FarmerListView.as_view(), name='farmer-list'),
    path('api/farmers/<int:pk>/', views.FarmerDetailView.as_view(), name='farmer-detail'),
    path('api/farmers/create/', views.FarmerCreateView.as_view(), name='farmer-create'),
    path('api/farmers/<int:pk>/update/', views.FarmerUpdateView.as_view(), name='farmer-update'),
    path('api/farmers/<int:pk>/delete/', views.FarmerDeleteView.as_view(), name='farmer-delete'),
]

