from django.urls import path
from . import views



urlpatterns = [
    
    # ✅ list of incomplete tasks associated with a specific client
    path('client/<int:client_id>', views.TaskListView.as_view(), name='task-list'),

    # ✅ list of incomplete tasks assigned to the current authenticated user
    path('my', views.UserAssignedTaskListView.as_view(), name='user-assigned-tasks'),  


    # Need to Test
    # Marks a task as completed for an authenticated user, validates task-specific requirements
    path('get/<int:task_id>/complete', views.CompleteTaskView.as_view(), name='complete-task'),  


    # ======================================== MY CUSTOM TASKS ===============================================

    # ✅ Retrieves all custom tasks assigned to the authenticated user
    path('mycustomtasks', views.UserCustomTaskListView.as_view(), name='user-custom-tasks'),

    # ✅ Updates the status or file of a custom task
    path('update-custom-task/<int:task_id>/', views.UpdateCustomTaskStatusView.as_view(), name='update-custom-task-status'),

]