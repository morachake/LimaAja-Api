from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from .models import (
  Farmer, Product, ProduceType, ProduceVariant, CooperativeProduce,
  Customer, Order, OrderItem, OrderReview,
  Transaction, BankAccount, Category
)
from rest_framework.permissions import IsAuthenticated
from .serializers import FarmerSerializer, ProductSerializer, FarmerDetailSerializer
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings
import os
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from django.db.models import Sum, Count, Q
from django.urls import reverse
import logging
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Set up logger
logger = logging.getLogger(__name__)

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

@method_decorator(csrf_exempt, name='dispatch')
class FarmerCreateView(generics.CreateAPIView):
    serializer_class = FarmerSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def perform_create(self, serializer):
        serializer.save(cooperative=self.request.user)
        
    def post(self, request, *args, **kwargs):
        # Check if this is a form submission
        if request.content_type == 'application/x-www-form-urlencoded':
            # Handle form submission
            data = {
                'name': request.POST.get('name'),
                'phone_number': request.POST.get('phone_number'),
                'location': request.POST.get('location')
            }
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                self.perform_create(serializer)
                messages.success(request, 'Farmer added successfully')
                return redirect('/cooperative/dashboard/?view=farmers')
            else:
                for field, errors in serializer.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                return redirect('/cooperative/dashboard/?view=farmers')
        
        # Handle API request
        return super().post(request, *args, **kwargs)

@method_decorator(csrf_exempt, name='dispatch')
class FarmerUpdateView(generics.UpdateAPIView):
    serializer_class = FarmerSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_queryset(self):
        return Farmer.objects.filter(cooperative=self.request.user)
        
    def put(self, request, *args, **kwargs):
        # Check if this is a form submission
        if request.content_type == 'application/x-www-form-urlencoded':
            # Handle form submission
            instance = self.get_object()
            data = {
                'name': request.POST.get('name'),
                'phone_number': request.POST.get('phone_number'),
                'location': request.POST.get('location')
            }
            serializer = self.get_serializer(instance, data=data)
            if serializer.is_valid():
                self.perform_update(serializer)
                messages.success(request, 'Farmer updated successfully')
                return redirect('/cooperative/dashboard/?view=farmers')
            else:
                for field, errors in serializer.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                return redirect('/cooperative/dashboard/?view=farmers')
        
        # Handle API request
        return super().put(request, *args, **kwargs)
    
    # Override this to handle POST requests for form submissions
    def post(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)

@method_decorator(csrf_exempt, name='dispatch')
class FarmerDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_queryset(self):
        return Farmer.objects.filter(cooperative=self.request.user)
        
    def delete(self, request, *args, **kwargs):
        # Check if this is a form submission
        if request.content_type == 'application/x-www-form-urlencoded':
            try:
                # Handle form submission
                instance = self.get_object()
                farmer_name = instance.name
                self.perform_destroy(instance)
                messages.success(request, f'Farmer "{farmer_name}" deleted successfully')
            except Exception as e:
                messages.error(request, f'Error deleting farmer: {str(e)}')
            
            # Redirect back to farmers page
            return redirect('/cooperative/dashboard/?view=farmers')
        
        # Handle API request
        return super().delete(request, *args, **kwargs)
    
    # Override this to handle POST requests for form submissions
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

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
              
              # Force refresh user from database to ensure we have the latest is_approved status
              user.refresh_from_db()
              
              logger.info(f"User {user.email} logged in. is_approved: {user.is_approved}, has_certificates: {bool(user.certificates)}")
              
              # If user is approved, go to dashboard regardless of certificates
              if user.is_approved:
                  logger.info(f"User {user.email} is approved, redirecting to dashboard")
                  return redirect('cooperative_dashboard')
              # If user has not uploaded documents yet, redirect to verification
              elif not user.certificates:
                  return redirect('cooperative_verification')
              # If user has uploaded documents but is not approved yet
              else:
                  return redirect('awaiting_verification')
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
  
  # Force refresh user from database to ensure we have the latest is_approved status
  request.user.refresh_from_db()
  
  # If user is already approved, redirect to dashboard
  if request.user.is_approved:
      logger.info(f"User {request.user.email} is approved, redirecting to dashboard from verification")
      return redirect('cooperative_dashboard')
  
  # If user has already uploaded documents, redirect to awaiting verification
  if request.user.certificates:
      return redirect('awaiting_verification')
  
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
              'message': 'Documents uploaded successfully. Your account is pending approval.',
              'redirect': reverse('awaiting_verification')
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
  
  # Force refresh user from database to ensure we have the latest is_approved status
  request.user.refresh_from_db()
  
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
def awaiting_verification(request):
  if request.user.role != 'cooperative':
      messages.error(request, 'Only cooperatives can access this page')
      return redirect('cooperative_login')
  
  # Force refresh user from database to ensure we have the latest is_approved status
  request.user.refresh_from_db()
  
  # If user is already approved, redirect to dashboard
  if request.user.is_approved:
      logger.info(f"User {request.user.email} is approved, redirecting to dashboard from awaiting_verification")
      return redirect('cooperative_dashboard')
  
  # If user hasn't uploaded documents and is not approved, redirect to verification
  if not request.user.certificates and not request.user.is_approved:
      return redirect('cooperative_verification')
  
  # Add debug information
  logger.info(f"User {request.user.email} is in awaiting_verification view")
  logger.info(f"is_approved status: {request.user.is_approved}")
  logger.info(f"certificates: {bool(request.user.certificates)}")
  
  return render(request, 'cooperative/awaiting_verification.html')



# Add these new views for bank account management

@login_required
def cooperative_dashboard(request):
    # Check if user is a cooperative
    if request.user.role != 'cooperative':
        messages.error(request, 'You do not have access to this page')
        return redirect('cooperative_login')

    # Force refresh user from database to ensure we have the latest is_approved status
    request.user.refresh_from_db()

    # Check if user is approved
    if not request.user.is_approved:
        logger.info(f"User {request.user.email} is not approved, redirecting from dashboard")
        if request.user.certificates:
            return redirect('awaiting_verification')
        else:
            return redirect('cooperative_verification')

    logger.info(f"User {request.user.email} is approved, accessing dashboard")

    view = request.GET.get('view', 'overview')
    category = request.GET.get('category', 'all')
    status = request.GET.get('status', 'all')

    if view == 'products':
        # Filter produce based on category
        produce_items = CooperativeProduce.objects.filter(cooperative=request.user)
        if category != 'all':
            produce_items = produce_items.filter(produce_type__category__slug=category)

        # Get produce types for the form
        produce_types = ProduceType.objects.all()

        # Get counts for each category
        context = {
            'view': view,
            'produce_items': produce_items,
            'produce_types': produce_types,
            'total_produce': CooperativeProduce.objects.filter(cooperative=request.user).count(),
            'vegetables_count': CooperativeProduce.objects.filter(cooperative=request.user, produce_type__category__slug='vegetables').count(),
            'fruits_count': CooperativeProduce.objects.filter(cooperative=request.user, produce_type__category__slug='fruits').count(),
            'nuts_count': CooperativeProduce.objects.filter(cooperative=request.user, produce_type__category__slug='nuts').count(),
            'herbs_count': CooperativeProduce.objects.filter(cooperative=request.user, produce_type__category__slug='herbs').count(),
            'grains_count': CooperativeProduce.objects.filter(cooperative=request.user, produce_type__category__slug='grains').count(),
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
    elif view == 'farmers':
        # Get all farmers for this cooperative
        farmers = Farmer.objects.filter(cooperative=request.user).order_by('-created_at')
        
        context = {
            'view': view,
            'farmers': farmers,
            'farmers_count': farmers.count(),
        }
    else:
        # Overview dashboard - Calculate all real statistics
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        last_month_start = (first_day_of_month - timedelta(days=1)).replace(day=1)
        last_month_end = first_day_of_month - timedelta(days=1)
        
        # Farmer statistics
        farmers = Farmer.objects.filter(cooperative=request.user)
        farmer_count = farmers.count()
        
        # New farmers this month
        new_farmers_count = farmers.filter(created_at__gte=first_day_of_month).count()
        
        # Farmers added last month
        last_month_farmers = farmers.filter(
            created_at__gte=last_month_start,
            created_at__lte=last_month_end
        ).count()
        
        # Calculate growth percentage
        farmer_growth = 0
        if last_month_farmers > 0:
            farmer_growth = round((new_farmers_count / last_month_farmers) * 100)
        
        # Order statistics
        orders = Order.objects.filter(cooperative=request.user)
        order_count = orders.count()
        
        # New orders this month
        new_orders_count = orders.filter(created_at__gte=first_day_of_month).count()
        
        # Orders from last month
        last_month_orders = orders.filter(
            created_at__gte=last_month_start,
            created_at__lte=last_month_end
        ).count()
        
        # Calculate order growth percentage
        order_growth = 0
        if last_month_orders > 0:
            order_growth = round((new_orders_count / last_month_orders) * 100)
        
        # Revenue statistics
        total_revenue = orders.filter(status='delivered').aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        # Revenue this month
        current_month_revenue = orders.filter(
            status='delivered',
            created_at__gte=first_day_of_month
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        # Revenue last month
        last_month_revenue = orders.filter(
            status='delivered',
            created_at__gte=last_month_start,
            created_at__lte=last_month_end
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        # Calculate revenue growth
        revenue_growth = 0
        if last_month_revenue > 0:
            revenue_growth = round((current_month_revenue / last_month_revenue - 1) * 100)
        
        # Order status counts for tracking
        processing_count = orders.filter(status='processing').count()
        transit_count = orders.filter(status='delivery').count()
        delivered_count = orders.filter(status='delivered').count()
        
        # Calculate percentages for progress bars
        total_tracked_orders = processing_count + transit_count + delivered_count
        if total_tracked_orders > 0:
            processing_percentage = round((processing_count / total_tracked_orders) * 100)
            transit_percentage = round((transit_count / total_tracked_orders) * 100)
            delivered_percentage = round((delivered_count / total_tracked_orders) * 100)
        else:
            processing_percentage = transit_percentage = delivered_percentage = 0
        
        # Get recent orders
        recent_orders = orders.order_by('-created_at')[:7]
        
        # Get produce items and category statistics
        produce_items = CooperativeProduce.objects.filter(cooperative=request.user)
        
        # Calculate category statistics
        categories_db = Category.objects.all().order_by('display_order')
        categories = []
        
        for category in categories_db:
            # Get produce items in this category for this cooperative
            cat_items = produce_items.filter(produce_type__category__slug=category.slug)
            cat_count = cat_items.count()
            cat_quantity = cat_items.aggregate(total=Sum('quantity'))['total'] or 0
            
            # Calculate percentage based on inventory levels
            max_expected = 100  # This could be a target or maximum expected inventory
            percentage = min(round((cat_quantity / max_expected) * 100) if max_expected > 0 else 0, 100)
            
            categories.append({
                'name': category.name,
                'slug': category.slug,
                'count': cat_count,
                'quantity': cat_quantity,
                'percentage': percentage,
                'remaining': cat_quantity,
                'icon': category.icon,
                'color': category.color
            })
        
        # Get recent farmers
        recent_farmers = farmers.order_by('-created_at')[:5]
        
        context = {
            'view': view,
            'farmers': recent_farmers,
            'produce_items': produce_items[:5],
            'recent_orders': recent_orders,
            
            # Farmer statistics
            'farmer_count': farmer_count,
            'new_farmers_count': new_farmers_count,
            'farmer_growth': farmer_growth,
            
            # Order statistics
            'order_count': order_count,
            'new_orders_count': new_orders_count,
            'order_growth': order_growth,
            
            # Revenue statistics
            'total_revenue': total_revenue,
            'revenue_growth': revenue_growth,
            'revenue_increase': current_month_revenue,
            
            # Order tracking
            'processing_count': processing_count,
            'transit_count': transit_count,
            'delivered_count': delivered_count,
            'processing_percentage': processing_percentage,
            'transit_percentage': transit_percentage,
            'delivered_percentage': delivered_percentage,
            
            # Categories
            'categories': categories,
            
            # Other stats
            'pending_orders_count': orders.filter(status__in=['new', 'processing', 'delivery']).count(),
            'completed_orders_count': delivered_count,
        }

    return render(request, 'cooperative/dashboard.html', context)



@login_required
def produce_detail(request, produce_type_id):
    # Check if user is a cooperative
    if request.user.role != 'cooperative':
        messages.error(request, 'You do not have access to this page')
        return redirect('cooperative_login')
    
    # Get the produce type
    produce_type = get_object_or_404(ProduceType, id=produce_type_id)
    
    # Get all variants of this produce type for this cooperative
    cooperative_produces = CooperativeProduce.objects.filter(
        cooperative=request.user,
        produce_type=produce_type
    )
    
    # Group by location to get provinces
    provinces = cooperative_produces.values_list('location', flat=True).distinct()
    
    # Calculate total quantity
    total_quantity = cooperative_produces.aggregate(total=Sum('quantity'))['total'] or 0
    
    # Prepare variants data
    variants = []
    for produce in cooperative_produces:
        variant_data = {
            'id': produce.id,
            'quantity': produce.quantity,
            'grade': produce.grade,
            'location': produce.location,
            'price': produce.produce_type.price_per_unit,
            'farmers_count': 1  # Placeholder, you might want to calculate this based on your data model
        }
        variants.append(variant_data)
    
    context = {
        'view': 'products',
        'produce_type': produce_type,
        'variants': variants,
        'total_variants': len(variants),
        'total_quantity': total_quantity,
        'provinces': provinces
    }
    
    return render(request, 'cooperative/dashboard/produce_detail.html', context)


@login_required
def add_produce(request):
  if request.method == 'POST':
      try:
          # Get form data
          produce_type_id = request.POST.get('produce_type')
          quantity = request.POST.get('quantity')
          location = request.POST.get('location')
          grade = request.POST.get('grade', 'A')  # Default to Grade A if not provided
          
          # Validate data
          if not produce_type_id or not quantity or not location:
              messages.error(request, 'Please fill in all required fields')
              return redirect('cooperative_dashboard')
          
          # Get the produce type
          produce_type = get_object_or_404(ProduceType, id=produce_type_id)
          
          # Create the cooperative produce
          CooperativeProduce.objects.create(
              cooperative=request.user,
              produce_type=produce_type,
              quantity=quantity,
              location=location,
              grade=grade
          )
          
          messages.success(request, f'{produce_type.name} added successfully')
      except Exception as e:
          messages.error(request, f'Error adding produce: {str(e)}')
      
      # Redirect back to the products page with view parameter
      return redirect('/cooperative/dashboard/?view=products')    
  # If not POST, redirect to dashboard
  return redirect('cooperative_dashboard')


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
          messages.success(request, f'Produce {produce.produce_type.name} updated successfully')
          
      except (CooperativeProduce.DoesNotExist, ProduceVariant.DoesNotExist) as e:
          messages.error(request, f'Error updating produce: {str(e)}')
      except Exception as e:
          messages.error(request, f'An unexpected error occurred: {str(e)}')

  # Redirect back to the products page with view parameter
  return redirect('/cooperative/dashboard/?view=products')

@login_required
def delete_produce(request, produce_id):
  if request.method == 'POST':
      try:
          produce = CooperativeProduce.objects.get(id=produce_id, cooperative=request.user)
          produce_name = produce.produce_type.name
          produce.delete()
          messages.success(request, f'Produce {produce_name} deleted successfully')
      except CooperativeProduce.DoesNotExist:
          messages.error(request, 'Produce not found')
      except Exception as e:
          messages.error(request, f'An unexpected error occurred: {str(e)}')

  # Redirect back to the products page with view parameter
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

@login_required
def request_money(request):
  if request.method == 'POST':
      amount = request.POST.get('amount')
      bank_account_id = request.POST.get('bank_account')
      notes = request.POST.get('notes', '')
      
      try:
          # Validate amount
          amount = float(amount)
          
          # Get wallet balance
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
          
          # Check if amount is valid
          if amount <= 0:
              messages.error(request, 'Amount must be greater than zero')
              return redirect('/cooperative/dashboard/?view=finance')
          
          if amount > wallet_balance:
              messages.error(request, f'You cannot request more than your available balance of RWF {wallet_balance:.2f}')
              return redirect('/cooperative/dashboard/?view=finance')
          
          # Get bank account
          bank_account = get_object_or_404(BankAccount, id=bank_account_id, cooperative=request.user)
          
          # Create a withdrawal request transaction
          reference_number = f"WD-{uuid.uuid4().hex[:8].upper()}"
          
          transaction = Transaction.objects.create(
              cooperative=request.user,
              transaction_type='sent',
              amount=amount,
              payment_method='wire_transfer',
              status='pending',
              party_name='Lima-Aja Admin',
              description=f"Withdrawal request to {bank_account.bank_name} account {bank_account.account_number}. {notes}",
              reference_number=reference_number
          )
          
          # Send notification to admin
          send_mail(
              'New Withdrawal Request',
              f'Cooperative {request.user.full_name} has requested a withdrawal of RWF {amount:.2f} to their {bank_account.bank_name} account. Reference: {reference_number}',
              settings.DEFAULT_FROM_EMAIL,
              [settings.ADMIN_EMAIL],
              fail_silently=True,
          )
          
          messages.success(request, f'Your withdrawal request for RWF {amount:.2f} has been submitted. Lima-Aja will process your request within 1-3 business days.')
          
      except ValueError:
          messages.error(request, 'Invalid amount')
      except BankAccount.DoesNotExist:
          messages.error(request, 'Invalid bank account')
      except Exception as e:
          messages.error(request, f'An error occurred: {str(e)}')
  
  return redirect('/cooperative/dashboard/?view=finance')

def dashboard_test(request):
  """
  A test view to debug dashboard styling issues
  """
  return render(request, 'cooperative/dashboard_base_test.html')

# Add this new view for logout
def logout_view(request):
  logout(request)
  messages.success(request, 'You have been successfully logged out.')
  return redirect('cooperative_login')

@login_required
def check_approval_status(request):
  """
  AJAX endpoint to check if a user's approval status has changed
  """
  if not request.user.is_authenticated or request.user.role != 'cooperative':
      return JsonResponse({'is_approved': False})
  
  # Force refresh from database to get the latest status
  request.user.refresh_from_db()
  
  # Log the check
  logger.info(f"Checking approval status for {request.user.email}: {request.user.is_approved}")
  
  return JsonResponse({'is_approved': request.user.is_approved})

# Add these new views for bank account management

@login_required
def add_bank_account(request):
    if request.method == 'POST':
        bank_name = request.POST.get('bank_name')
        account_number = request.POST.get('account_number')
        account_holder_name = request.POST.get('account_holder_name')
        is_primary = request.POST.get('is_primary') == 'on'
        
        # Check if user already has 2 bank accounts
        existing_accounts = BankAccount.objects.filter(cooperative=request.user).count()
        if existing_accounts >= 2:
            messages.error(request, 'You can have a maximum of 2 bank accounts. Please delete an existing account first.')
            return redirect('/cooperative/dashboard/?view=finance')
        
        try:
            # Create bank account
            BankAccount.objects.create(
                cooperative=request.user,
                bank_name=bank_name,
                account_number=account_number,
                account_holder_name=account_holder_name,
                is_primary=is_primary
            )
            
            messages.success(request, 'Bank account added successfully')
        except Exception as e:
            messages.error(request, f'Error adding bank account: {str(e)}')
    
    return redirect('/cooperative/dashboard/?view=finance')

@login_required
def delete_bank_account(request, account_id):
    if request.method == 'POST':
        try:
            account = BankAccount.objects.get(id=account_id, cooperative=request.user)
            
            # Check if this is the only account and it's being used in pending transactions
            is_only_account = BankAccount.objects.filter(cooperative=request.user).count() == 1
            has_pending_transactions = Transaction.objects.filter(
                cooperative=request.user,
                status='pending',
                description__icontains=account.account_number
            ).exists()
            
            if is_only_account and has_pending_transactions:
                messages.error(request, 'Cannot delete this account as it is being used in pending transactions')
                return redirect('/cooperative/dashboard/?view=finance')
            
            # If this is a primary account, set another account as primary
            if account.is_primary:
                other_account = BankAccount.objects.filter(cooperative=request.user).exclude(id=account_id).first()
                if other_account:
                    other_account.is_primary = True
                    other_account.save()
            
            account.delete()
            messages.success(request, 'Bank account deleted successfully')
        except BankAccount.DoesNotExist:
            messages.error(request, 'Bank account not found')
        except Exception as e:
            messages.error(request, f'Error deleting bank account: {str(e)}')
    
    return redirect('/cooperative/dashboard/?view=finance')

@login_required
def set_primary_bank_account(request, account_id):
    if request.method == 'POST':
        try:
            account = BankAccount.objects.get(id=account_id, cooperative=request.user)
            
            # Set this account as primary
            account.is_primary = True
            account.save()
            
            messages.success(request, 'Primary bank account updated successfully')
        except BankAccount.DoesNotExist:
            messages.error(request, 'Bank account not found')
        except Exception as e:
            messages.error(request, f'Error updating primary bank account: {str(e)}')
    
    return redirect('/cooperative/dashboard/?view=finance')
