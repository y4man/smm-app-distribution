from django.urls import path
from . import views



urlpatterns = [

    # Testing Required

    # Need to apply the otp api 
    path('signup', views.UserSignupView.as_view(), name='client-signup'),  # Self-signup

    # Create and list client with web Dev Data(business_name, contact_person, adress, email_address)
    path('webdev', views.ClientWebDevDataListCreateView.as_view(), name='clients-list-create'),

    path('webdev/<int:pk>', views.ClientWebDevDataDetailView.as_view(), name='client-detail'),
    
    # 
    path('<int:pk>/assign-team', views.AssignClientToTeamView.as_view(), name='assign-client-to-team'),

    path('<int:client_id>/update-workflow', views.UpdateClientWorkflowView.as_view(), name='update-client-workflow'),

 
    path('<int:client_id>/proposal', views.UploadProposalView.as_view(), name='upload-proposal'),
    
    # HTTP 200 ok
    path('<int:client_id>/invoices', views.ClientInvoicesListCreateView.as_view(), name='client-invoices-list-create'),

    # HTTPS 200 ok 
    path('<int:client_id>/invoices/<int:pk>', views.ClientInvoicesRetrieveUpdateDeleteView.as_view(), name='client-invoices-rud'),

    # HTTP 404 (Not Found) (need to test properly)
    path('invoices/approve', views.ApproveInvoiceView.as_view(), name='approve-invoice'),

    # HTTP 404 (Not Found) (need to test properly)
    path('invoices/reject', views.RejectInvoiceView.as_view(), name='reject-invoice'),

    # Client Plans (you have to link the plan with account manager)
    path('<int:client_id>/plans', views.ClientPlanView.as_view(), name='client-plan-list-create'),

    path('monthly-reports/<int:client_id>/<str:month_name>', views.ClientMonthlyReportsListCreateView.as_view(), name='monthly_reports_list_create'),

    path('monthly-reports/<int:pk>', views.ClientMonthlyReportsRUDView.as_view(), name='monthly_reports_rud'),

    path('<int:client_id>/client-team', views.ClientTeamView.as_view(), name='client-team'),

    path('<int:client_id>/custom-tasks', views.ClientCustomTaskView.as_view(), name='client-custom-tasks'),
]