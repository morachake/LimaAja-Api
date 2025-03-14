from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import (
    Farmer, Product, ProduceType, ProduceVariant, CooperativeProduce,
    Customer, Order, OrderItem, OrderReview,
    Transaction, BankAccount
)
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
from django.db.models import Sum, Count, Q

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
                    
                    # Create directory  request.user.email, file.name)
                    
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
    
    view = request.GET.get('view', 'overview')
    category = request.GET.get('category', 'all')
    status = request.GET.get('status', 'all')
    
    if view == 'products':
        # Filter produce based on category
        produce_items = CooperativeProduce.objects.filter(cooperative=request.user)
        if category != 'all':
            produce_items = produce_items.filter(produce_type__category=category)
    
        # Get produce types for the form
        produce_types = ProduceType.objects.all()
    
        # Get counts for each category
        context = {
            'view': view,
            'produce_items': produce_items,
            'produce_types': produce_types,
            'total_produce': CooperativeProduce.objects.filter(cooperative=request.user).count(),
            'vegetables_count': CooperativeProduce.objects.filter(cooperative=request.user, produce_type__category='vegetables').count(),
            'fruits_count': CooperativeProduce.objects.filter(cooperative=request.user, produce_type__category='fruits').count(),
            'nuts_count': CooperativeProduce.objects.filter(cooperative=request.user, produce_type__category='nuts').count(),
            'herbs_count': CooperativeProduce.objects.filter(cooperative=request.user, produce_type__category='herbs').count(),
            'grains_count': CooperativeProduce.objects.filter(cooperative=request.user, produce_type__category='grains').count(),
            'view_mode': request.GET.get('view_mode', 'grid'),
        }
    elif view == 'orders':
        # Filter orders based on status
        orders = Order.objects.filter(cooperative=request.user)
        if status != 'all':
            orders = orders.filter(status=status)
        
        # Get counts for each status
        context = {
            'view': view,
            'status': status,
            'orders': orders,
            'all_count': Order.objects.filter(cooperative=request.user).count(),
            'new_count': Order.objects.filter(cooperative=request.user, status='new').count(),
            'processing_count': Order.objects.filter(cooperative=request.user, status='processing').count(),
            'delivery_count': Order.objects.filter(cooperative=request.user, status='delivery').count(),
            'delivered_count': Order.objects.filter(cooperative=request.user, status='delivered').count(),
            'cancelled_count': Order.objects.filter(cooperative=request.user, status='cancelled').count(),
        }
    elif view == 'finance':
        # Get wallet balance (sum of received minus sent)
        received_amount = Transaction.objects.filter(
            cooperative=request.user, 
            transaction_type='received',
            status='success'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        sent_amount = Transaction.objects.filter(
            cooperative=request.user, 
            transaction_type='sent',
            status='success'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        wallet_balance = received_amount - sent_amount
        
        # Get bank accounts
        bank_accounts = BankAccount.objects.filter(cooperative=request.user)
        
        # Get recent transactions
        transactions = Transaction.objects.filter(cooperative=request.user).order_by('-created_at')[:10]
        
        # Get transaction counts
        all_transactions_count = Transaction.objects.filter(cooperative=request.user).count()
        received_count = Transaction.objects.filter(cooperative=request.user, transaction_type='received').count()
        sent_count = Transaction.objects.filter(cooperative=request.user, transaction_type='sent').count()
        
        # Get spending data for chart (last 7 days)
        today = timezone.now().date()
        spending_data = []
        for i in range(7):
            day = today - timezone.timedelta(days=i)
            day_spending = Transaction.objects.filter(
                cooperative=request.user,
                transaction_type='sent',
                status='success',
                created_at__date=day
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            spending_data.append({
                'day': day.strftime('%a'),
                'amount': float(day_spending)
            })
        
        # Reverse to show oldest to newest
        spending_data.reverse()
        
        context = {
            'view': view,
            'wallet_balance': wallet_balance,
            'bank_accounts': bank_accounts,
            'transactions': transactions,
            'all_transactions_count': all_transactions_count,
            'received_count': received_count,
            'sent_count': sent_count,
            'spending_data': spending_data
        }
    else:
        # Overview dashboard
        context = {
            'view': view,
            'farmers': Farmer.objects.filter(cooperative=request.user),
            'produce_items': CooperativeProduce.objects.filter(cooperative=request.user),
            'recent_orders': Order.objects.filter(cooperative=request.user).order_by('-created_at')[:5],
            'order_count': Order.objects.filter(cooperative=request.user).count(),
            'produce_count': CooperativeProduce.objects.filter(cooperative=request.user).count(),
            'farmer_count': Farmer.objects.filter(cooperative=request.user).count()
        }
    
    return render(request, 'cooperative/dashboard.html', context)

@login_required
def produce_detail(request, produce_type_id):
    produce_type = get_object_or_404(ProduceType, id=produce_type_id)
    variants = CooperativeProduce.objects.filter(
        cooperative=request.user,
        produce_type=produce_type
    ).select_related('variant')
    
    # Group variants by grade
    variants_by_grade = {}
    total_quantity = 0
    for variant in variants:
        if variant.variant.grade not in variants_by_grade:
            variants_by_grade[variant.variant.grade] = {
                'grade': variant.variant.grade,
                'price': variant.produce_type.base_price * variant.variant.price_multiplier,
                'quantity': variant.quantity,
                'provinces': [variant.province],
                'farmers_count': 3  # Placeholder - implement actual count
            }
        else:
            variants_by_grade[variant.variant.grade]['quantity'] += variant.quantity
            if variant.province not in variants_by_grade[variant.variant.grade]['provinces']:
                variants_by_grade[variant.variant.grade]['provinces'].append(variant.province)
        total_quantity += variant.quantity
    
    # Sort variants by grade
    sorted_variants = sorted(variants_by_grade.values(), key=lambda x: x['grade'])
    
    context = {
        'produce_type': produce_type,
        'variants': sorted_variants,
        'total_variants': len(variants_by_grade),
        'total_quantity': total_quantity
    }
    
    return render(request, 'cooperative/produce_detail.html', context)

@login_required
def add_produce(request):
    if request.method == 'POST':
        produce_type_id = request.POST.get('produce_type')
        variant_grade = request.POST.get('variants[]')  # Changed from variants to variants[]
        quantity = request.POST.get('quantity')
        province = request.POST.get('province')
        
        try:
            produce_type = ProduceType.objects.get(id=produce_type_id)
            variant = ProduceVariant.objects.get(
                produce_type=produce_type,
                grade=variant_grade
            )
            
            # Create the cooperative produce
            CooperativeProduce.objects.create(
                cooperative=request.user,
                produce_type=produce_type,
                variant=variant,
                quantity=quantity,
                province=province
            )
            
            messages.success(request, 'Produce added successfully')
            
        except (ProduceType.DoesNotExist, ProduceVariant.DoesNotExist) as e:
            messages.error(request, f'Error adding produce: {str(e)}')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
    
    return redirect('/cooperative/dashboard/?view=products')

@login_required
def update_produce(request, produce_id):
    if request.method == 'POST':
        try:
            produce = CooperativeProduce.objects.get(id=produce_id, cooperative=request.user)
            
            # Update fields
            variant_grade = request.POST.get('variant')
            quantity = request.POST.get('quantity')
            province = request.POST.get('province')
            
            if variant_grade:
                variant = ProduceVariant.objects.get(produce_type=produce.produce_type, grade=variant_grade)
                produce.variant = variant
            
            if quantity:
                produce.quantity = quantity
                
            if province:
                produce.province = province
            
            produce.save()
            messages.success(request, 'Produce updated successfully')
            
        except (CooperativeProduce.DoesNotExist, ProduceVariant.DoesNotExist) as e:
            messages.error(request, f'Error updating produce: {str(e)}')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
    
    # Redirect back to the products page
    return redirect('/cooperative/dashboard/?view=products')

@login_required
def delete_produce(request, produce_id):
    if request.method == 'POST':
        try:
            produce = CooperativeProduce.objects.get(id=produce_id, cooperative=request.user)
            produce.delete()
            messages.success(request, 'Produce deleted successfully')
        except CooperativeProduce.DoesNotExist:
            messages.error(request, 'Produce not found')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
    
    # Redirect back to the products page
    return redirect('/cooperative/dashboard/?view=products')

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, cooperative=request.user)
    
    context = {
        'order': order,
        'items': order.items.all(),
        'review': OrderReview.objects.filter(order=order).first(),
        'transactions': Transaction.objects.filter(order=order)
    }
    
    return render(request, 'cooperative/dashboard/order_detail.html', context)

@login_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, cooperative=request.user)
        new_status = request.POST.get('status')
        
        if new_status in dict(Order.STATUS_CHOICES).keys():
            order.status = new_status
            order.save()
            messages.success(request, f'Order status updated to {order.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('order_detail', order_id=order_id)

def dashboard_test(request):
    """
    A test view to debug dashboard styling issues
    """
    return render(request, 'cooperative/dashboard_base_test.html')

