from django.contrib import admin
from .models import ClientInvoices, ClientWorkflowState

# Register your models here.
admin.site.register(ClientInvoices)
admin.site.register(ClientWorkflowState)