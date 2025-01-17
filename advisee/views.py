import threading

from pprint import pprint

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as loginUser, logout as logoutUser
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.urls import reverse

from advisor.models import Advisor, Topic, Mail

from .forms import AdviseeRegistrationForm
from .forms import AdviseeLoginForm
from .models import Advisee
from .decorators import advisee_login_required
from .utils import regenerate_advisee_topic_instructions

@advisee_login_required
def message_send (request):
    advisee = Advisee.objects.get(user_id=request.user.id)
    advisor = advisee.advisor

    message_body = request.POST['reply-textarea'].strip()

    if (message_body != ""):
        mail = Mail(
            sender = advisee.user,
            receiver = advisor.user,
            body = message_body
        )
        mail.save()
    
    return redirect(reverse("advisee:message_inbox"))

@advisee_login_required
def message_inbox(request):
    advisee = Advisee.objects.get(user_id=request.user.id)
    advisor = advisee.advisor

    all_mails_reults = Mail.objects.filter(Q(sender=advisee.user) | Q(receiver=advisee.user)).order_by("sent_at")

    all_mails = []
    for mail in all_mails_reults:
        all_mails.append({
            'sender': f"{mail.sender.first_name} {mail.sender.last_name}",
            'receiver': f"{mail.receiver.first_name} {mail.receiver.last_name}",
            'sent_at': mail.sent_at.strftime("%B %d '%y - %I:%M %p"),
            'unread_class': 'fa-circle' if mail.unread and mail.receiver == advisee.user else '',
            'body': mail.body.replace("\n", "<br/>")
        })

        if mail.unread and mail.receiver == advisee.user:
            mail.unread = False
            mail.save()

    return render(request, 'advisee/message/inbox.html', {
        'advisor': advisor,
        'all_mails' : all_mails
    })

@advisee_login_required
def dashboard(request):
    advisee = Advisee.objects.get(user_id=request.user.id)
    topics = Topic.objects.filter(active=True).order_by("order")

    # if form was saved
    if (request.method == 'POST'):
        curIndustry = advisee.industry
        newIndustry = request.POST.get("industry").strip()

        # if the industry has changed:
        if (curIndustry != newIndustry):
            # set new industry in advisee and empty out topic instructions
            advisee.industry = newIndustry
            advisee.topic_instructions = "{}"
            advisee.save()

            # if newIndustry is not empty, regnereate topic instructions in background thread
            if (newIndustry):
                def background_task():
                    regenerate_advisee_topic_instructions(advisee.id)
                
                thread = threading.Thread(target=background_task)
                thread.start()

        # save new topic texts
        for topic in topics:
            if request.POST.get("topic-"+str(topic.id)):
                advisee.set_topic_text(topic.id, request.POST.get("topic-"+str(topic.id)))

        advisee.save()


    # compile topic data for template
    topics_data = []
    for topic in topics: 
        topics_data.append({
            'id': topic.id,
            'name': topic.name,
            'instruction_text': advisee.get_topic_instruction(topic.id)["text"].replace('\n', '<br>'), 
            'instruction_unread': advisee.get_topic_instruction(topic.id)["unread"], 
            'text': advisee.get_topic_text(topic.id)
        })

    return render(request, 'advisee/dashboard.html', {
        'advisee': advisee,
        'topics_data': topics_data
    })

def index(request):
    return render(request, 'advisee/index.html')

def logout(request):
    logoutUser(request)
    return redirect('/advisee')

def login(request):
    form_errors = None;

    if request.method == 'POST':
        form = AdviseeLoginForm(request, request.POST)
        if form.is_valid():
            loginUser(request, form.get_user())

            username = form.cleaned_data.get('username')
            messages.success(request, 'Welcome ' + username + '!')

            return redirect('/advisee/dashboard')
        else:
            form_errors = form.errors.get("__all__")
    else:
        form = AdviseeLoginForm()

    return render(request, 'advisee/login.html', {'form':form, 'form_errors':form_errors})

def register(request):
    if request.method == 'POST':
        form = AdviseeRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
            
                    advisee = Advisee.objects.create(user=user)
            except Exception as e:
                print(f"Exception: {e}")
            else:
                # username = form.cleaned_data.get('username')
                messages.success(request, 'Account was created for ' + user.username + '. You can now login!')

            return redirect('/advisee/login/')
    else:
        form = AdviseeRegistrationForm()
    
    return render(request, 'advisee/register.html', {'form':form})

# Recieves request to load Chatbot page for the advisee
@advisee_login_required
def chatbot(request):
    return render(request, "advisee/chatbot.html")