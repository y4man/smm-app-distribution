from django.urls import path
from . import views


urlpatterns = [
        # ========================= PLAN MANAGEMENT ROUTES =========================

    # ✅ List or create plans     
    path('', views.ListCreatePlanView.as_view(), name='plan-list-create'),

    # ✅ Retrieve, update, or delete a  single plan
    path('<int:pk>', views.RetrieveUpdateDestroyPlanView.as_view(), name='plan-rud'),

    # ✅ Assign Plan to Manager
    path('<int:pk>/assign', views.PlanAssignView.as_view(), name='assign-plan-to-managers'),

    # ✅ List Plan Assigned to the client's Account Manager
    path('<int:client_id>/account-manager-plans', views.AssignedPlansForAccountManagerView.as_view(), name='assigned-plans-for-account-manager'),

    # ✅ Remove an Account Manager from Plan (Server Error 500)
    path('remove-account-manager', views.RemoveAccountManagerFromPlanView.as_view(), name='removed-account-managers-from-plan'),

    # ✅ List Account Manager not yet assigned to a plan (GET not allowed)(not just AM)
    path('search-unassigned-account-managers', views.UnassignedAccountManagerSearchView.as_view(), name='search-unassigned-account-managers'),

    # ✅ List all account Manager who are assigned to a specific plan
    path('assigned-account-managers-list/', views.AssignedAccountManagerSearchView.as_view(), name='search-assigned-account-managers'),

]