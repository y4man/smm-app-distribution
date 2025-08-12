from django.contrib import admin
from .models import Task, CustomTask

# Register your models here.
admin.site.register(Task)
admin.site.register(CustomTask)