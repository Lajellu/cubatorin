from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .models import Advisor

def advisor_login_required(view_func):
    def wrapper_func (request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # return HttpResponseForbidden("Access Forbidden: You are not logged in")
            return redirect('/advisor/login')

        if not Advisor.objects.filter(user_id=request.user.id).exists():
            # return HttpResponseForbidden("Access Forbidden: You are not an Advisor")
            return redirect('/advisor/login')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper_func
