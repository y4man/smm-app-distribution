from django.urls import path
from . import views

urlpatterns = [
    
    # ✅
    path('profile', views.ProfileView.as_view(), name='profile'),

    # ✅
    path('profile/update', views.UpdateProfileView.as_view(), name='update_profile'),

    # ✅
    path('', views.ListUsersView.as_view(), name='list-users'),

    # ✅
    path('create', views.AdminCreateUserView.as_view(), name='create-user'),

    # ✅
    path('get/<int:id>', views.UsersView.as_view(), name='user'),

    # ❌
    path('get/by-role',views.UserListByRoleView.as_view(), name='users-by-role'),
]
