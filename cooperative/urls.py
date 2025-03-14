from django.urls import path, include
from .views import (
    cooperative_index, cooperative_login, cooperative_register, cooperative_verification,
    cooperative_dashboard, document_upload, dashboard_test,
    FarmerListView, FarmerDetailView, FarmerCreateView, FarmerUpdateView, FarmerDeleteView,
    add_produce, update_produce, delete_produce, produce_detail,
    order_detail, update_order_status
)

urlpatterns = [
    # Template-based URLs for cooperative portal
    path('', cooperative_index, name='cooperative_index'),
    path('login/', cooperative_login, name='cooperative_login'),
    path('register/', cooperative_register, name='cooperative_register'),
    path('verification/', cooperative_verification, name='cooperative_verification'),
    path('dashboard/', cooperative_dashboard, name='cooperative_dashboard'),
    path('document-upload/', document_upload, name='document_upload'),
    path('dashboard-test/', dashboard_test, name='dashboard_test'),
    
    # Produce management URLs
    path('produce/<int:produce_type_id>/', produce_detail, name='produce_detail'),
    path('add-produce/', add_produce, name='add_produce'),
    path('update-produce/<int:produce_id>/', update_produce, name='update_produce'),
    path('delete-produce/<int:produce_id>/', delete_produce, name='delete_produce'),
    
    # Order management URLs
    path('order/<int:order_id>/', order_detail, name='order_detail'),
    path('order/<int:order_id>/update-status/', update_order_status, name='update_order_status'),
    
    # API endpoints for cooperative data
    path('api/', include([
        # Farmer endpoints
        path('farmers/', FarmerListView.as_view(), name='farmer-list'),
        path('farmers/<int:pk>/', FarmerDetailView.as_view(), name='farmer-detail'),
        path('farmers/create/', FarmerCreateView.as_view(), name='farmer-create'),
        path('farmers/<int:pk>/update/', FarmerUpdateView.as_view(), name='farmer-update'),
        path('farmers/<int:pk>/delete/', FarmerDeleteView.as_view(), name='farmer-delete'),
    ])),
]

