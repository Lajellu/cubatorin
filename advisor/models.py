from django.contrib.auth.models import User
from django.db import models
from django.db.models import Model
from django.utils import timezone

class Advisor(Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Advisor({self.id}:{self.user.username})"

class Topic(Model):
    name = models.CharField(max_length=255)
    active = models.BooleanField(blank=False, null=False, default=True)
    order = models.IntegerField(blank=False, null=False, default=1)

    def __str__(self):
        return f"Topic({self.id}:{self.name})"

class Article(Model):
    # SUMMARIZE-PROCESSING ---> UPLOADDATA-PROCESSING ----> FINETUNE-PROCESSING ----> FINETUNE-SUCCEEDED ----> ACCEPTED 
    #                      └---> SUMMARIZE-FAILED     └--> UPLOADDATA-FAILED    └---> FINETUNE-FAILED    └---> REJECTED
    STATUS_CHOICES = [
        ('SUMMARIZE-PROCESSING', 'Summarize Processing'),
        ('SUMMARIZE-FAILED', 'Summarize Failed'),
        ('UPLOADDATA-PROCESSING', 'Upload Data Processing'),
        ('UPLOADDATA-FAILED', 'Upload Data Failed'),
        ('FINETUNE-PROCESSING', 'Finetune Processing'),
        ('FINETUNE-FAILED', 'Finetune Failed'),
        ('FINETUNE-SUCCEEDED', 'Finetune Succeeded'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]

    advisor =               models.ForeignKey(Advisor, on_delete=models.CASCADE)
    topic =                 models.ForeignKey(Topic, on_delete=models.CASCADE)
    name =                  models.CharField(max_length=200)
    uploaded_on =           models.DateTimeField(default=timezone.now)
    status =                models.CharField(max_length=100, choices=STATUS_CHOICES, default='SUMMARIZE-PROCESSING')
    failure_reason =        models.TextField(blank=False, null=False, default='')
    body =                  models.TextField(blank=False, null=False, default='')
    summary =               models.TextField(blank=False, null=False, default='')
    finetune_checkpoints =  models.TextField(blank=False, null=False, default='')
    finetune_metrics =      models.TextField(blank=False, null=False, default='')
    test_query =            models.CharField(max_length=1000, blank=False, null=False, default='')
    test_result =           models.TextField(blank=False, null=False, default='')

    def __str__(self):
        return f"Article({self.id}:{self.name} -on- {self.topic.name})"

#  Internal one-to-one mail system 
class Mail(Model):

    sender = models.ForeignKey(User, related_name='sent_mails', on_delete=models.DO_NOTHING)
    receiver = models.ForeignKey(User, related_name='received_mails', on_delete=models.DO_NOTHING)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    unread = models.BooleanField(default=True)
    read_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Mail({self.id}:{self.sender} --> {self.receiver} on {self.sent_at})"
