from . import models
# from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
# from django.core.mail import send_mail
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from account.models import CustomUser

# NEW 
def create_task(client, task_type, user):
    """
    Create or update a task for the given client and user.
    If the task was completed, it updates the existing task to the next step.
    """
    try:
        # Check if a task of the same type already exists for the client
        existing_task = models.Task.objects.filter(client=client, task_type=task_type).first()
        
        if existing_task:
            # If the existing task is completed, update it instead of creating a new one
            if existing_task.is_completed:
                print(f"Updating completed task '{task_type}' for client '{client.business_name}'.")
                existing_task.is_completed = False  # Reset the completion status
                existing_task.assigned_to = user  # Reassign to the new user
                existing_task.save(update_fields=['is_completed', 'assigned_to'])
                return existing_task
            else:
                # If the task is not completed, update the assigned user if necessary
                if existing_task.assigned_to != user:
                    print(f"Re-assigning task '{task_type}' from '{existing_task.assigned_to}' to '{user}'")
                    existing_task.assigned_to = user
                    existing_task.save(update_fields=['assigned_to'])
                print(f"Task '{task_type}' for client '{client.business_name}' already exists and is not completed. Skipping task creation.")
                return existing_task

        # If no existing task, create a new task
        print(f"Creating task: {task_type} for client: {client.business_name} assigned to: {user.username}")
        task = models.Task.objects.create(client=client, assigned_to=user, task_type=task_type, is_completed=False)
        print(f"Task created successfully: {task}")
        return task

    except models.Task.DoesNotExist:
        # If no task exists, create a new one
        print(f"No existing task found. Creating new task: {task_type} for client: {client.business_name} assigned to: {user.username}")
        task = models.Task.objects.create(client=client, assigned_to=user, task_type=task_type, is_completed=False)
        return task

    except ValidationError as e:
        print(f"Validation error when creating task: {e}")
    except Exception as e:
        print(f"Error when creating task: {e}")

# NEW 24-01-25
def mark_task_as_completed(task, current_user, reassign_to_marketing=False):
    """
    Mark a task as completed and create or update the next task in the workflow.
    """
    print(f"Completing task: {task.task_type} for client: {task.client.business_name}")
    task.is_completed = True
    task.save()
    TASK_TYPE_MAPPING = {
        "assign_client_to_team": "Assign Client to Team",
        "create_proposal": "Create Proposal",
        "approve_proposal": "Approve Proposal",
        "schedule_brief_meeting": "Schedule Brief Meeting",
        "is_meeting_completed": "Check Meeting Completion",
        "assigned_plan_to_client": "Assign Plan to Client",
        "create_strategy": "Create Strategy",
        "content_writing": "Write Content",
        "approve_content_by_marketing_manager": "Approve Content (Marketing Manager)",
        "approve_content_by_account_manager": "Approve Content (Account Manager)",
        "creatives_design": "Design Creatives",
        "approve_creatives_by_marketing_manager": "Approve Creatives (Marketing Manager)",
        "approve_creatives_by_account_manager": "Approve Creatives (Account Manager)",
        "schedule_onboarding_meeting": "Schedule Onboarding Meeting",
        "onboarding_meeting": "Onboarding Meeting",
        "smo_scheduling": "Schedule SMO",
        "invoice_submission": "Submit Invoice",
        "invoice_verification": "Verify Invoice",
        "payment_confirmation": "Confirm Payment",
        "schedule_meeting": "Schedule Meeting",
        "brief_meeting": "Brief Meeting",
        "monthly_reporting": "Monthly Reporting",
    }
    # Notify the current user (task completer)
    # send_task_notification(
    #     recipient=current_user,
    #     message=f"You have successfully completed the task '{TASK_TYPE_MAPPING.get(task.task_type, task.task_type)}'.",
    #     notification_type="task_completed"
    # )
    # Determine the next step and the user to assign the task to
    if reassign_to_marketing:
        print(f"Reassigning task to marketing manager for client: {task.client.business_name}")
        next_step = "create_proposal"
        next_user = get_team_member_by_role("marketing_manager", task)
    else:
        next_step, next_user = get_next_step_and_user(task)
    if not next_step or not next_user:
        print(f"No next step or user found for task: {task.task_type}. Workflow may have reached an end or is misconfigured.")
        return
    print(f"Next step: {next_step}, Next user: {next_user}")
    # Check if a similar task already exists for the client and next step
    existing_task = models.Task.objects.filter(client=task.client, task_type=next_step).first()
    if existing_task:
        if existing_task.is_completed:
            print(f"Reactivating existing task for next step '{next_step}' for client '{task.client.business_name}'")
            existing_task.is_completed = False
            existing_task.assigned_to = next_user
            existing_task.save(update_fields=["is_completed", "assigned_to"])
            # Notify the next user about the reactivated task
            send_task_notification(
                recipient=next_user,
                message=f"A task '{TASK_TYPE_MAPPING.get(next_step, next_step)}' has been reactivated and assigned to you.",
                task=task,  # Pass the current task object to include the task details
                notification_type="task_assigned"
            )
        else:
            print(f"Task '{next_step}' for client '{task.client.business_name}' is already in progress.")
        return existing_task
    else:
        # Create a new task for the next step
        print(f"Creating new task for next step '{next_step}' for client '{task.client.business_name}', assigned to: {next_user.username}")
        new_task = create_task(task.client, next_step, next_user)
        # Notify the next user about the new task
        send_task_notification(
            recipient=new_task.assigned_to,
            message=f"New task '{TASK_TYPE_MAPPING.get(next_step, next_step)}' has been assigned to you.",
            task=new_task,
            notification_type="task_assigned"
        )
        return new_task
        
def update_client_workflow(client, next_step):
    """Update the client's workflow to the next step."""
    workflow_state, _ = models.ClientWorkflowState.objects.get_or_create(client=client)
    workflow_state.current_step = next_step
    workflow_state.save()

def get_team_member_by_role(role_name, task):
    team = task.client.team
    """Fetch the team member or global member based on role_name."""
        
    # Fetch from team members for team-specific roles
    if role_name in ['marketing_manager', 'content_writer', 'marketing_assistant', 'graphics_designer']:
        member = task.client.team.memberships.filter(user__role=role_name).first()
        if member:
            print(f"Found team-specific member for role '{role_name}' in team '{task.client.team.name}': {member.user}")
            return member.user
        else:
            print(f"Error: Role '{role_name}' not found in team '{task.client.team.name}'")
            return None

    # Fetch 'account_manager' from the client or team
    if role_name == 'account_manager':
        account_manager = task.client.account_manager
        if account_manager:
            print(f"Found client-specific account manager: {account_manager}")
            return account_manager
        else:
            # If no client-specific account manager, check the team
            member = task.client.team.memberships.filter(user__role='account_manager').first()
            if member:
                print(f"Found team-specific account manager: {member.user}")
                return member.user
            print(f"Error: Account manager not found for client or team.")
            return None

    # Fetch global roles like 'accountant' or 'marketing_director'
    if role_name in ['accountant', 'marketing_director']:
        global_user = CustomUser.objects.filter(role=role_name).first()
        if global_user:
            print(f"Found global member for role '{role_name}': {global_user}")
            return global_user
        else:
            print(f"Error: Global role '{role_name}' not found")
            return None

    print(f"Error: Role '{role_name}' is not recognized.")
    return None

def get_next_step_and_user(task):
    """Determine the next step and user in the workflow."""
    
    # Workflow mapping with the appropriate roles and next steps
    workflow_mapping = {
        'assign_team': ('create_proposal', get_team_member_by_role('marketing_manager', task)),
        'create_proposal': ('approve_proposal', get_team_member_by_role('account_manager', task)),
        'approve_proposal': check_proposal_status(task),
        'schedule_brief_meeting': ('is_meeting_completed', get_team_member_by_role('account_manager', task)),  # New step after schedule_brief_meeting
        'is_meeting_completed': ('assigned_plan_to_client', get_team_member_by_role('account_manager', task)),  # Proceed to the next step after meeting completion
        'assigned_plan_to_client': ('create_strategy', get_team_member_by_role('marketing_manager', task)),  
        'create_strategy': ('content_writing', get_team_member_by_role('content_writer', task)),
        'content_writing': ('approve_content_by_marketing_manager', get_team_member_by_role('marketing_manager', task)),
        'approve_content_by_marketing_manager': ('approve_content_by_account_manager', get_team_member_by_role('account_manager', task)),
        'approve_content_by_account_manager': ('creatives_design', get_team_member_by_role('graphics_designer', task)),
        'creatives_design': ('approve_creatives_by_marketing_manager', get_team_member_by_role('marketing_manager', task)),
        'approve_creatives_by_marketing_manager': ('approve_creatives_by_account_manager', get_team_member_by_role('account_manager', task)),
        'approve_creatives_by_account_manager': ('schedule_onboarding_meeting', get_team_member_by_role('account_manager', task)),
        'schedule_onboarding_meeting': ('onboarding_meeting', get_team_member_by_role('account_manager', task)),
        'onboarding_meeting': ('smo_scheduling', get_team_member_by_role('marketing_assistant', task)),
        'smo_scheduling': ('invoice_submission', get_team_member_by_role('accountant', task)),
        'invoice_submission': ('invoice_verification', get_team_member_by_role('account_manager', task)),
        'invoice_verification': ('payment_confirmation', get_team_member_by_role('accountant', task)),
        'payment_confirmation': ('schedule_meeting', get_team_member_by_role('account_manager', task)),
        'schedule_meeting': ('brief_meeting', get_team_member_by_role('account_manager', task)),
        'brief_meeting': ('create_strategy', get_team_member_by_role('marketing_manager', task)),
        'monthly_reporting': ('invoice_submission', get_team_member_by_role('accountant', task)),
    } 

    current_step = task.task_type

    while current_step:
        next_step, next_user = workflow_mapping.get(current_step, (None, None))

        # Special handling for `assigned_plan_to_client`
        if current_step == 'assigned_plan_to_client' and task.client.client_plans.exists():
            print(f"Skipping 'assigned_plan_to_client' for client '{task.client.business_name}'.")
            current_step = 'create_strategy'  # Skip to `create_strategy`
            

        # Return the next step and user if valid
        if next_step and next_user:
            print(f"Next step: {next_step}, assigned to: {next_user}")
            return next_step, next_user

        # Handle end of workflow
        print(f"No next step found for task type: {current_step}")
        return None, None

def check_proposal_status(task):
    """Check the client's proposal approval status and return the next step and user."""
    client = task.client
    proposal_status = client.proposal_approval_status
    print(f"Checking proposal status for client '{client.business_name}': {proposal_status}")

    if proposal_status == 'approved':
        next_user = client.account_manager
        return 'schedule_brief_meeting', next_user
    elif proposal_status == 'changes_required':
        next_user = client.team.memberships.filter(user__role='marketing_manager').first().user
        return 'create_proposal', next_user
    elif proposal_status == 'declined':
        return None, None
    else:
        # Default behavior when no status is set
        next_user = client.team.memberships.filter(user__role='marketing_manager').first().user
        return 'create_proposal', next_user

def update_client_status(client, status):
    """Update the client's overall status."""
    client_status, _ = models.ClientStatus.objects.get_or_create(client=client)
    client_status.status = status
    client_status.save()

# New 24-01-25
def send_task_notification(recipient, message, task=None, notification_type="info", sender=None):
    """
    Send a notification to a user and save it to the database.
    Store history for actions performed by the user.
    """
    try:
        # Default values for thread_notify
        client_id = None
        client_name = None
        task_type = None

        if task:
            client_id = task.client.id
            client_name = task.client.business_name
            task_type = task.task_type

        print(f"Preparing to send notification to recipient {recipient.id} ({recipient.get_full_name()}).")

        # Save notification to the database with new fields
        notification = models.Notification.objects.create(
            recipient=recipient,
            sender=sender,
            message=message,
            notification_type=notification_type,
            is_read=False,
            client_id=client_id,
            client_name=client_name,
            task_type=task_type,
        )

        # Save history entry
        if sender:
            action_text = f"{sender.get_full_name()} ({sender.role}) performed action: '{message}'"
        else:
            action_text = f"{message}"

        history_entry = models.History.objects.create(
            user=sender if sender else recipient,  # Use sender if available, otherwise recipient
            action=action_text
        )

        print(f"History recorded: {action_text}")

        # Send notification via WebSocket
        channel_layer = get_channel_layer()
        group_name = f"notifications_{recipient.id}"  # Use the user-specific group name
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "notification": {
                    "id": notification.id,
                    "client_id": client_id,
                    "client_name": client_name,
                    "task_type": task_type,
                    "sender_id": sender.id if sender else None,
                    "sender_name": sender.get_full_name() if sender else None,
                    "recipient": recipient.id,
                    "recipient_full_name": recipient.get_full_name(),
                    "recipient_role": recipient.role,
                    "is_read": notification.is_read,
                    "notification_type": notification_type,
                    "message": message,
                },
            },
        )
        print(f"Notification sent successfully to recipient {recipient.id}.")
    except Exception as e:
        print(f"Failed to send notification: {e}")

