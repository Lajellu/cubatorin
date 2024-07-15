from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as loginUser, logout as logoutUser
from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from pprint import pprint


from .forms import AdvisorRegistrationForm
from .forms import AdvisorLoginForm
from .models import Advisor, Article, Topic
from .decorators import advisor_login_required
from advisee.models import Advisee

@advisor_login_required
def dashboard(request):
    advisor_id = Advisor.objects.get(user_id=request.user.id)
    num_advisees = Advisee.objects.filter(advisor_id=advisor_id).count()
    num_articles = Article.objects.filter(advisor_id=advisor_id).count()

    num_articles_per_topic = Topic.objects.annotate(num_articles=Count('article')).values('id','name','num_articles')
    perc_articles_per_topic = []
    for row in num_articles_per_topic:
        perc_articles_per_topic.append({'topic_name':row['name'], 'perc_complete':int(row['num_articles']/30*100)})

    return render(request, 'advisor/dashboard.html', {
        'user':request.user, 
        'num_advisees':num_advisees,
        'num_articles':num_articles,
        'perc_articles_per_topic':perc_articles_per_topic,
        })

def index(request):
    return render(request, 'advisor/index.html')

def logout(request):
    logoutUser(request)
    return redirect('/advisor')

def login(request):
    form_errors = None;

    if request.method == 'POST':
        form = AdvisorLoginForm(request, request.POST)
        if form.is_valid():
            loginUser(request, form.get_user())
            return redirect('/advisor/dashboard')
        else:
            form_errors = form.errors.get("__all__")
    else:
        form = AdvisorLoginForm()

    return render(request, 'advisor/login.html', {'form':form, 'form_errors':form_errors})

def register(request):
    if request.method == 'POST':
        form = AdvisorRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
            
                    advisor = Advisor.objects.create(user=user)
            except Exception as e:
                print(f"Exception: {e}")
            else:
                # username = form.cleaned_data.get('username')
                messages.success(request, 'Account was created for ' + user.username + '. You can now login!')

            return redirect('/advisor/login/')
    else:
        form = AdvisorRegistrationForm()
    
    return render(request, 'advisor/register.html', {'form':form})
