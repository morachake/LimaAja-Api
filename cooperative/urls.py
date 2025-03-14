from django.urls import path, include
from .views import (
    cooperative_index, cooperative_login, cooperative_register, cooperative_verification,
    cooperative_dashboard, document_upload, dashboard_test,
    FarmerListView, FarmerDetailView, FarmerCreateView, FarmerUpdateView, FarmerDeleteView,
    ProductListView, ProductDetailView, ProductCreateView, ProductUpdateView, ProductDeleteView,
    add_produce
)

urlpatterns = [
    # Template-based URLs for cooperative portal
    path('', cooperative_index, name='cooperative_index'),
    path('login/', cooperative_login, name='cooperative_login'),
    path('register/', cooperative_register, name='cooperative_register'),
    path('verification/', cooperative_verification, name='cooperative_verification'),
    path('dashboard/', cooperative_dashboard, name='cooperative_dashboard'),
    path('document-upload/', document_upload, name='document_upload'),
    path('dashboard-test/', dashboard_test, name='dashboard_test'),  # Added test route
    path('add-produce/', add_produce, name='add_produce'),  # Add this line
    
    # API endpoints for cooperative data
    path('api/', include([
        # Farmer endpoints
        path('farmers/', FarmerListView.as_view(), name='farmer-list'),
        path('farmers/<int:pk>/', FarmerDetailView.as_view(), name='farmer-detail'),
        path('farmers/create/', FarmerCreateView.as_view(), name='farmer-create'),
        path('farmers/<int:pk>/update/', FarmerUpdateView.as_view(), name='farmer-update'),
        path('farmers/<int:pk>/delete/', FarmerDeleteView.as_view(), name='farmer-delete'),
        
        # Product endpoints
        path('products/', ProductListView.as_view(), name='product-list'),
        path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
        path('products/create/', ProductCreateView.as_view(), name='product-create'),
        path('products/<int:pk>/update/', ProductUpdateView.as_view(), name='product-update'),
        path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),
    ])),
]

