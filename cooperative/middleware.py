from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
import logging

# Set up logger
logger = logging.getLogger(__name__)

class CooperativeAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request before view is called
        if request.user.is_authenticated and request.user.role == 'cooperative':
            # Force refresh user from database to ensure we have the latest is_approved status
            request.user.refresh_from_db()
            
            # Get the current path
            current_path = request.path
            
            # Exclude certain paths from redirection
            excluded_paths = [
                reverse('cooperative_verification'),
                reverse('awaiting_verification'),
                reverse('cooperative_dashboard'),
                reverse('logout'),
                '/static/',
                '/media/',
                '/admin/',
                '/api/',
                '/check-approval-status/',
            ]
            
            # Check if the current path is in the excluded paths
            is_excluded = any(current_path.startswith(path) for path in excluded_paths)
            
            if not is_excluded:
                logger.info(f"Middleware checking user {request.user.email}, is_approved: {request.user.is_approved}, has_certificates: {bool(request.user.certificates)}")
                
                # First check if user is approved - if so, they can access everything
                if request.user.is_approved:
                    logger.info(f"User {request.user.email} is approved, allowing access")
                    # No redirection needed, user is approved
                    pass
                # If user hasn't uploaded documents, redirect to verification
                elif not request.user.certificates:
                    logger.info(f"Middleware redirecting user {request.user.email} to verification")
                    return redirect('cooperative_verification')
                # If user has uploaded documents but is not approved yet
                else:
                    logger.info(f"Middleware redirecting user {request.user.email} to awaiting verification")
                    return redirect('awaiting_verification')

        response = self.get_response(request)
        return response

