from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Farmer, Product
from .serializers import FarmerSerializer, ProductSerializer, FarmerDetailSerializer
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings
import os
from django.utils import timezone

User = get_user_model()

# Existing API views...
class IsApprovedCooperative(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'cooperative' and request.user.is_approved

class FarmerListView(generics.ListAPIView):
    serializer_class = FarmerSerializer
    permission_classes = [IsApprovedCooperative]

    def get_queryset(self):
        return Farmer.objects.filter(cooperative=self.request.user)

class FarmerDetailView(generics.RetrieveAPIView):
    serializer_class = FarmerDetailSerializer
    permission_classes = [IsApprovedCooperative]

    def get_queryset(self):
        return Farmer.objects.filter(cooperative=self.request.user)

class FarmerCreateView(generics.CreateAPIView):
    serializer_class = FarmerSerializer
    permission_classes = [IsApprovedCooperative]

    def perform_create(self, serializer):
        serializer.save(cooperative=self.request.user)

class FarmerUpdateView(generics.UpdateAPIView):
    serializer_class = FarmerSerializer
    permission_classes = [IsApprovedCooperative]

    def get_queryset(self):
        return Farmer.objects.filter(cooperative=self.request.user)

class FarmerDeleteView(generics.DestroyAPIView):
    permission_classes = [IsApprovedCooperative]

    def get_queryset(self):
        return Farmer.objects.filter(cooperative=self.request.user)

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsApprovedCooperative]

    def get_queryset(self):
        return Product.objects.filter(cooperative=self.request.user)

class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsApprovedCooperative]

    def get_queryset(self):
        return Product.objects.filter(cooperative=self.request.user)

class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsApprovedCooperative]

    def perform_create(self, serializer):
        farmer = get_object_or_404(Farmer, id=self.request.data.get('farmer'), cooperative=self.request.user)
        serializer.save(cooperative=self.request.user, farmer=farmer)

class ProductUpdateView(generics.UpdateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsApprovedCooperative]

    def get_queryset(self):
        return Product.objects.filter(cooperative=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        farmer_id = request.data.get('farmer')
        if farmer_id:
            farmer = get_object_or_404(Farmer, id=farmer_id, cooperative=self.request.user)
            request.data['farmer'] = farmer.id
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class ProductDeleteView(generics.DestroyAPIView):
    permission_classes = [IsApprovedCooperative]

    def get_queryset(self):
        return Product.objects.filter(cooperative=self.request.user)


# New template-based views for cooperatives
def cooperative_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user is not None and user.role == 'cooperative':
            login(request, user)
            if not user.is_approved:
                return redirect('document_upload')
            return redirect('cooperative_dashboard')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'cooperative/login.html')

def cooperative_register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'cooperative/register.html')
        
        try:
            user = User.objects.create_user(
                email=email,
                full_name=full_name,
                phone_number=phone_number,
                password=password,
                role='cooperative',
                is_approved=False
            )
            login(request, user)
            return redirect('document_upload')
        except Exception as e:
            messages.error(request, str(e))
    
    return render(request, 'cooperative/register.html')

@login_required
def document_upload(request):
    if request.user.role != 'cooperative':
        messages.error(request, 'Only cooperatives can access this page')
        return redirect('cooperative_login')
    
    if request.user.is_approved:
        return redirect('cooperative_dashboard')
    
    if request.method == 'POST':
        certificates = []
        
        # Handle certificate uploads
        for file_key in request.FILES:
            if file_key.startswith('certificate'):
                file = request.FILES[file_key]
                file_path = os.path.join('certificates', request.user.email, file.name)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.join(settings.MEDIA_ROOT, 'certificates', request.user.email), exist_ok=True)
                
                # Save file
                with open(os.path.join(settings.MEDIA_ROOT, file_path), 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                
                certificates.append({
                    'name': file.name,
                    'path': file_path,
                    'uploaded_at': str(timezone.now())
                })
        
        # Update user certificates
        if certificates:
            request.user.certificates = certificates
            request.user.save()
            messages.success(request, 'Documents uploaded successfully. Your account is pending approval.')
    
    return render(request, 'cooperative/document_upload.html')

@login_required
def cooperative_dashboard(request):
    if request.user.role != 'cooperative' or not request.user.is_approved:
        messages.error(request, 'You do not have access to this page')
        return redirect('cooperative_login')
    
    farmers = Farmer.objects.filter(cooperative=request.user)
    products = Product.objects.filter(cooperative=request.user)
    
    context = {
        'farmers': farmers,
        'products': products
    }
    
    return render(request, 'cooperative/dashboard.html', context)

