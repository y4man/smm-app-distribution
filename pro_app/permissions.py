from rest_framework.permissions import BasePermission
class RoleBasedPermission(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        user = request.user
        allowed_roles = getattr(self, 'allowed_roles', [])
        return user.is_authenticated and getattr(user, 'role', '').lower() in [role.lower() for role in allowed_roles]

class IsMarketingDirector(RoleBasedPermission):
    allowed_roles = ['marketing_director', 'Marketing Director']
class IsMarketingManager(RoleBasedPermission):
    allowed_roles = ['marketing_manager']
class IsAccountManager(RoleBasedPermission):
    allowed_roles = ['account_manager']
class IsUsernIsAccountManager(RoleBasedPermission):
    allowed_roles = ['user', 'account_manager']
class IsAccountant(RoleBasedPermission):
    allowed_roles = ['accountant']
class IsMarketingTeam(RoleBasedPermission):
    allowed_roles = ['account_manager', 'marketing_manager', 'marketing_assistant', 'content_writer', 'graphics_designer']
# CUSTOM PERMISSION for marketing director and account manager
class IsMarketingDirectorOrAccountManager(BasePermission):
    """
    Custom permission that allows access to users with either 'marketing_director' or 'account_manager' roles.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['marketing_director', 'account_manager']
    
class IsMarketingmanagerOrAccountManager(BasePermission):
    """
    Custom permission that allows access to users with either 'marketing_manager' or 'account_manager' roles.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['marketing_manager', 'account_manager']
    
class AccountantOrAccountManager(BasePermission):
    """
    Custom permission that allows access to users with either 'accountant' or 'account_manager' roles.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['accountant', 'account_manager']

