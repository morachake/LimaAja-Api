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
from django.http import JsonResponse
from django.core.mail import send_mail

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


def cooperative_index(request):
    return render(request, 'cooperative/index.html')

# login for coopreratives
def cooperative_login(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(phone_number=phone_number)
            user = authenticate(request, email=user.email, password=password)
            
            if user is not None and user.role == 'cooperative':
                login(request, user)
                
                # If user has not uploaded documents yet, redirect to verification
                if not user.certificates:
                    return redirect('cooperative_verification')
                # If user is not approved, show message but still allow dashboard access
                elif not user.is_approved:
                    messages.info(request, 'Your account is pending approval.')
              
                return redirect('cooperative_dashboard')
            else:
                messages.error(request, 'Invalid phone number or password')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this phone number')
    
    return render(request, 'cooperative/login.html')

def cooperative_register(request):
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        # Validate passwords
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'cooperative/register.html')
        
        try:
            # Create user
            user = User.objects.create_user(
                email=email,
                full_name=full_name,
                phone_number=phone_number,
                password=password,
                role='cooperative',
                is_approved=False
            )
            
            messages.success(request, 'Registration successful! Please log in to continue with verification.')
            return redirect('cooperative_login')
        except Exception as e:
            messages.error(request, str(e))
    
    return render(request, 'cooperative/register.html')

@login_required
def cooperative_verification(request):
    if request.user.role != 'cooperative':
        messages.error(request, 'Only cooperatives can access this page')
        return redirect('cooperative_login')
    
    if request.user.is_approved:
        return redirect('cooperative_dashboard')
    
    if request.method == 'POST':
        certificates = []
        
        for file_key in request.FILES:
            if file_key.startswith('documents'):
                for file in request.FILES.getlist(file_key):
                    # Validate file type
                    if not file.content_type in ['image/svg+xml', 'image/png', 'image/jpeg', 'image/gif']:
                        return JsonResponse({
                            'success': False,
                            'message': f'Invalid file type for {file.name}. Only SVG, PNG, JPG or GIF files are allowed.'
                        })
                    
                    # Validate file size (5MB limit)
                    if file.size > 5 * 1024 * 1024:
                        return JsonResponse({
                            'success': False,
                            'message': f'File {file.name} is too large. Maximum size is 5MB.'
                        })
                    
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
            if request.user.certificates:
                existing_certs = request.user.certificates
                if isinstance(existing_certs, list):
                    existing_certs.extend(certificates)
                    request.user.certificates = existing_certs
                else:
                    request.user.certificates = certificates
            else:
                request.user.certificates = certificates
            
            request.user.save()
            
            # Send notification to admin
            send_mail(
                'New Cooperative Documents Uploaded',
                f'Cooperative {request.user.full_name} has uploaded verification documents.',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=True,
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Documents uploaded successfully. Your account is pending approval.'
            })
        
        return JsonResponse({
            'success': False,
            'message': 'No documents were uploaded.'
        })
    
    return render(request, 'cooperative/verification.html')


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
    if request.user.role != 'cooperative':
        messages.error(request, 'You do not have access to this page')
        return redirect('cooperative_login')
    
    # Get the view parameter from the URL
    view = request.GET.get('view', 'overview')
    
    # Handle form submissions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            # Update user profile
            request.user.full_name = request.POST.get('full_name')
            request.user.phone_number = request.POST.get('phone_number')
            request.user.address = request.POST.get('address')
            request.user.city = request.POST.get('city')
            request.user.country = request.POST.get('country')
            request.user.save()
            messages.success(request, 'Profile updated successfully')
            
        elif action == 'change_password':
            # Change password
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match')
            else:
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Password changed successfully')
    
    # Get data for the dashboard
    farmers = Farmer.objects.filter(cooperative=request.user)
    products = Product.objects.filter(cooperative=request.user)
    
    context = {
        'view': view,
        'farmers': farmers,
        'products': products
    }
    
    return render(request, 'cooperative/dashboard.html', context)

@login_required
def add_produce(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        farmer_id = request.POST.get('farmer')
        
        try:
            farmer = Farmer.objects.get(id=farmer_id, cooperative=request.user)
            
            Product.objects.create(
                cooperative=request.user,
                farmer=farmer,
                name=name,
                description=description,
                price=price,
                quantity=quantity
            )
            
            messages.success(request, 'Product added successfully')
            return redirect('cooperative_dashboard')
            
        except Farmer.DoesNotExist:
            messages.error(request, 'Invalid farmer selected')
    
    return redirect('cooperative_dashboard')

def dashboard_test(request):
    """
    A test view to debug dashboard styling issues
    """
    return render(request, 'cooperative/dashboard_base_test.html')

