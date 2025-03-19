from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import (
  Farmer, Product, ProduceType, ProduceVariant, CooperativeProduce,
  Customer, Order, OrderItem, OrderReview,
  Transaction, BankAccount
)
from .serializers import FarmerSerializer, ProductSerializer, FarmerDetailSerializer
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings
import os
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from django.db.models import Sum, Count, Q
from django.urls import reverse
import logging
import uuid

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
      produce_items = CooperativeProduce.objects.filter(cooperative=request.user).order_by('-created_at')
      recent_orders = Order.objects.filter(cooperative=request.user).order_by('-created_at')[:5]
      
      # Get counts for dashboard cards
      produce_count = produce_items.count()
      farmer_count = Farmer.objects.filter(cooperative=request.user).count()
      order_count = Order.objects.filter(cooperative=request.user).count()
      
      # Calculate total revenue
      total_revenue = Order.objects.filter(
          cooperative=request.user, 
          status='delivered'
      ).aggregate(total=Sum('total_price'))['total'] or 0
      
      # Get category counts for produce summary
      category_counts = {}
      total_quantity = 0
      most_common_category = None
      max_count = 0
      
      for produce in produce_items:
          category = produce.produce_type.get_category_display()
          if category in category_counts:
              category_counts[category] += 1
          else:
              category_counts[category] = 1
              
          if category_counts[category] > max_count:
              max_count = category_counts[category]
              most_common_category = category
              
          total_quantity += produce.quantity
      
      # Get order status counts
      pending_orders_count = Order.objects.filter(
          cooperative=request.user, 
          status__in=['new', 'processing', 'delivery']
      ).count()
      
      completed_orders_count = Order.objects.filter(
          cooperative=request.user, 
          status='delivered'
      ).count()
      
      # Calculate average order value
      avg_order_value = 0
      if order_count > 0:
          avg_order_value = Order.objects.filter(
              cooperative=request.user
          ).aggregate(avg=Sum('total_price') / order_count)['avg'] or 0
      
      # Get order status distribution
      order_status_counts = {}
      for status_choice, status_display in Order.STATUS_CHOICES:
          count = Order.objects.filter(cooperative=request.user, status=status_choice).count()
          if count > 0:
              order_status_counts[status_display] = count
      
      context = {
          'view': view,
          'farmers': Farmer.objects.filter(cooperative=request.user),
          'produce_items': produce_items[:5],
          'recent_orders': recent_orders,
          'produce_count': produce_count,
          'farmer_count': farmer_count,
          'order_count': order_count,
          'total_revenue': total_revenue,
          'category_counts': category_counts,
          'most_common_category': most_common_category,
          'total_quantity': total_quantity,
          'pending_orders_count': pending_orders_count,
          'completed_orders_count': completed_orders_count,
          'avg_order_value': avg_order_value,
          'order_status_counts': order_status_counts,
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

