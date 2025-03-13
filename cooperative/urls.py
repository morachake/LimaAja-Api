from django.urls import path, include
from .views import (
    cooperative_login, cooperative_register, document_upload, cooperative_dashboard,
    FarmerListView, FarmerDetailView, FarmerCreateView, FarmerUpdateView, FarmerDeleteView,
    ProductListView, ProductDetailView, ProductCreateView, ProductUpdateView, ProductDeleteView
)

urlpatterns = [
    # Template-based URLs
    path('login/', cooperative_login, name='cooperative_login'),
    path('register/', cooperative_register, name='cooperative_register'),
    path('dashboard/', cooperative_dashboard, name='cooperative_dashboard'),
    path('document-upload/', document_upload, name='document_upload'),
    
    # API endpoints
    path('v1/', include([
        path('farmers/', FarmerListView.as_view(), name='farmer-list'),
        path('farmers/<int:pk>/', FarmerDetailView.as_view(), name='farmer-detail'),
        path('farmers/create/', FarmerCreateView.as_view(), name='farmer-create'),
        path('farmers/<int:pk>/update/', FarmerUpdateView.as_view(), name='farmer-update'),
        path('farmers/<int:pk>/delete/', FarmerDeleteView.as_view(), name='farmer-delete'),
        
        path('products/', ProductListView.as_view(), name='product-list'),
        path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
        path('products/create/', ProductCreateView.as_view(), name='product-create'),
        path('products/<int:pk>/update/', ProductUpdateView.as_view(), name='product-update'),
        path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),
    ])),
]

