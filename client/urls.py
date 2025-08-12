from django.urls import path
from . import views



urlpatterns = [

    # Testing Required

    # ✅ Need to apply the otp api 
    path('signup', views.UserSignupView.as_view(), name='client-signup'),  # Self-signup

    # ✅ Create and list client with web Dev Data(business_name, contact_person, adress, email_address)
    path('webdev', views.ClientWebDevDataListCreateView.as_view(), name='clients-list-create'),

    # ✅
    path('webdev/<int:pk>', views.ClientWebDevDataDetailView.as_view(), name='client-detail'),
    
    # ✅
    path('assign-team/<int:pk>', views.AssignClientToTeamView.as_view(), name='assign-client-to-team'),

    # Tested
    path('updateworkflow/<int:client_id>', views.UpdateClientWorkflowView.as_view(), name='update-client-workflow'),

    # need to test
    path('proposal/<int:client_id>', views.UploadProposalView.as_view(), name='upload-proposal'),
    

    # HTTP 200 ok (need to test properly)
    path('invoices/<int:client_id>', views.ClientInvoicesListCreateView.as_view(), name='client-invoices-list-create'),

    # HTTPS 200 ok (need to test properly)
    path('invoices/<int:client_id>/get/<int:pk>', views.ClientInvoicesRetrieveUpdateDeleteView.as_view(), name='client-invoices-rud'),

    # HTTP 404 (Not Found) (need to test properly)
    path('invoices/approve/', views.ApproveInvoiceView.as_view(), name='approve-invoice'),

    # HTTP 404 (Not Found) (need to test properly)
    path('invoices/reject/', views.RejectInvoiceView.as_view(), name='reject-invoice'),

    # ✅ Client Plans (you have to link the plan with account manager)
    path('plan/<int:client_id>/', views.ClientPlanView.as_view(), name='client-plan-list-create'),

    path('reports/<int:client_id>/<str:month_name>', views.ClientMonthlyReportsListCreateView.as_view(), name='monthly_reports_list_create'),

    path('reports/<int:pk>', views.ClientMonthlyReportsRUDView.as_view(), name='monthly_reports_rud'),

    path('team/<int:client_id>/', views.ClientTeamView.as_view(), name='client-team'),

    path('tasks/<int:client_id>/', views.ClientCustomTaskView.as_view(), name='client-custom-tasks'),
]