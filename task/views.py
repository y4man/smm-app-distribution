from datetime import datetime, timedelta
import os
import tempfile
from arrow import now
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status, generics
from pro_app.utils import check_proposal_status, create_task, get_next_step_and_user, mark_task_as_completed, send_task_notification, update_client_status
from pro_app import storage
from client.models import ClientInvoices
from calender.models import ClientCalendar, ClientCalendarDate 
from pro_app.models import Meeting
from .models import Task, CustomTask
from .serializers import CustomTaskSerializer, MyTaskSerializer, TaskSerializer
from storage3.exceptions import StorageApiError


# Create your views here.
class CompleteTaskView(APIView): 
    permission_classes = [IsAuthenticated]  

    def post(self, request, task_id):
        # Fetch the task using the task ID
        task = get_object_or_404(Task, id=task_id)

        # Extract `calendar_id` from the request data
        calendar_id = request.data.get("calendar_id")
        meeting_id = request.data.get("meeting_id")
        invoice_id = request.data.get("invoice_id")
        
        # Ensure the user is authorized to complete the task
        if request.user != task.assigned_to:
            return Response({"error": "You are not authorized to complete this task."}, status=status.HTTP_403_FORBIDDEN)

        # Ensure the client is assigned to a team
        if not task.client.team:
            return Response({"error": f"Client '{task.client.business_name}' is not assigned to a team."}, status=status.HTTP_400_BAD_REQUEST)

        # Handle already completed task
        if task.is_completed:
            return self._handle_completed_task(task)

        # Perform task-specific checks (e.g., meeting completion for 'schedule_meeting')
        task_check_result = self._perform_task_checks(request, task, calendar_id, meeting_id, invoice_id)
        if not task_check_result["success"]:
            return Response({"error": task_check_result["message"]}, status=status.HTTP_400_BAD_REQUEST)

        # Mark the task as completed and pass the current user
        mark_task_as_completed(task, current_user=request.user)

        # Handle updates to the client's status
        self._handle_client_status_update(task)

        return Response({"message": "Task completed successfully."}, status=status.HTTP_200_OK)

    def _perform_task_checks(self, request, task, calendar_id=None, meeting_id=None, invoice_id=None):
        """Perform task-specific checks before marking a task as completed."""
        
        if task.task_type == 'create_proposal' and not task.client.proposal_pdf:
            return {"success": False, "message": f"Proposal not uploaded for client: {task.client.business_name}."}

        if task.task_type == 'approve_proposal':
            return self._handle_approve_proposal_task(task, request)
   
        if task.task_type == 'schedule_brief_meeting':  # Check for brief meeting
            return self._check_brief_meeting_created(task, request, meeting_id)

        if task.task_type == 'schedule_onboarding_meeting':  # Check for at least 2 meetings
            return self._check_schedule_meeting_created(task, request, meeting_id)
         
        if task.task_type == 'assigned_plan_to_client':
            # Check if a plan has been assigned to the client
            client_plan_exists = task.client.client_plans.exists()  # Checks if any ClientsPlan exists for the client
            if not client_plan_exists:
                return {"success": False, "message": f"No plan is assigned to client '{task.client.business_name}'. Please assign a plan before completing this task."}

        if task.task_type == 'create_strategy':
            return self._check_calendar_resources(task, request, calendar_id)

        if task.task_type == 'content_writing':
            return self._check_content_availability(task, request, calendar_id) 
        
        if task.task_type == 'creatives_design':
            return self._check_creatives_design_task(task, request, calendar_id)
 
        if task.task_type == 'approve_content_by_marketing_manager':
            return self._handle_approve_content_by_marketing_manager(task, request, calendar_id)
        
        if task.task_type == 'approve_content_by_account_manager':
            return self._handle_approve_content_by_account_manager(task, request, calendar_id)
        
        if task.task_type == 'approve_creatives_by_marketing_manager':
            return self._handle_approve_creatives_by_marketing_manager(task, request, calendar_id)
        
        if task.task_type == 'approve_creatives_by_account_manager':
            return self._handle_approve_creatives_by_account_manager(task, request, calendar_id)

        if task.task_type == 'invoice_submission':
            return self._check_latest_month_invoice_submission(task, request, invoice_id)
        
        if task.task_type == 'invoice_verification':
            return self._check_invoice_verification(task, request, invoice_id)
        
        if task.task_type == 'payment_confirmation':
            return self._check_payment_status(task, request, invoice_id)
        
        if task.task_type == 'smo_scheduling':
            return self._update_smo_flag(task, request, calendar_id)
       
        return {"success": True}
    
    def _handle_completed_task(self, task):
        next_step, next_user = get_next_step_and_user(task)

        if next_step and next_user:
            print(f"Creating next task: {next_step} assigned to {next_user.username} for client {task.client.business_name}")
            create_task(task.client, next_step, next_user)
            return Response({"message": f"Next task '{next_step}' created successfully."}, status=status.HTTP_200_OK)

        print("No further steps found. Workflow complete or misconfigured.")
        return Response({"message": "Task completed, but no further steps available."}, status=status.HTTP_400_BAD_REQUEST)

        # next_step, next_user = get_next_step_and_user(task)
        # if next_step and next_user:
        #     create_task(task.client, next_step, next_user)
        #     return Response({"message": "Next task created as previous task was already completed."}, status=status.HTTP_200_OK)
        # return Response({"message": "This task has already been completed and no next step is available."}, status=status.HTTP_400_BAD_REQUEST)

    def _handle_approve_proposal_task(self, task, request):
        """
        Handle the proposal approval process by account managers.
        """
        client = task.client

        # Get the status from the request
        status = request.data.get('status')  # Expecting 'status' in the request data
        if not status:
            return {"success": False, "message": "The 'status' field is required for updating the task."}
        
        # Handle the different status cases
        if status == 'approve':
            # Update proposal status and proceed to the next task
            client.proposal_approval_status = 'approved'
            client.save()

            # Proceed to the next task
            next_step, next_user = check_proposal_status(task)
            if next_step and next_user:
                mark_task_as_completed(task, current_user=request.user)
                create_task(client, next_step, next_user)
                return {"success": True, "message": "Proposal approved and task completed successfully."}
            else:
                return {"success": True, "message": "Proposal approved, but no further steps are defined in the workflow."}

        elif status == 'changes_required':
            # Update proposal status and reassign task to the previous step
            client.proposal_approval_status = 'changes_required'
            client.save()

            # Get the previous step and reassign the task
            next_step, next_user = check_proposal_status(task)
            if next_step == 'create_proposal' and next_user:
                mark_task_as_completed(task, current_user=request.user)
                create_task(client, next_step, next_user)
                return {
                    "success": True,
                    "message": f"Proposal for client '{client.business_name}' requires changes. Task has been reassigned to the marketing manager."
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to reassign the task for changes required. Ensure the workflow is correctly configured."
                }

        elif status == 'declined':
            # Update proposal status and stop the workflow
            client.proposal_approval_status = 'declined'
            client.save()
            mark_task_as_completed(task, current_user=request.user)
            return {
                "success": False,
                "message": f"Proposal for client '{client.business_name}' has been declined. Workflow will not proceed further."
            }

        else:
            # Invalid status provided
            return {
                "success": False,
                "message": f"Invalid status '{status}' provided. Allowed statuses are: 'approve', 'changes_required', or 'declined'."
            }
            
    def _handle_client_status_update(self, task):
        """Handles the client status update after task completion, if needed."""
        if task.task_type == 'payment_confirmation':
            print(f"Updating client status to 'Completed' for client: {task.client.business_name}")
            update_client_status(task.client, 'Completed')

    def _check_brief_meeting_created(self, task, request, meeting_id):
        """
        ✅ Ensure a specific **brief meeting** (by `meeting_id`) exists before proceeding.
        ✅ Allows scheduling **next month’s meeting** in the current month.
        """

        client = task.client
        current_date = datetime.now().date()
        current_year, current_month = current_date.year, current_date.month

        # 🔹 Get next month & year
        next_month_date = current_date.replace(day=28) + timedelta(days=4)  
        next_month, next_year = next_month_date.month, next_month_date.year  

        # ✅ Step 1: Fetch the **specific meeting** using `meeting_id`
        try:
            meeting = Meeting.objects.get(id=meeting_id, client=client)
        except Meeting.DoesNotExist:
            return {
                "success": False,
                "message": f"⚠️ No meeting found with ID `{meeting_id}` for client '{client.business_name}'."
            }

        # ✅ Step 2: Check if the meeting is in **current or next month**
        if meeting.date.year == current_year and (meeting.date.month == current_month or meeting.date.month == next_month):
            # ✅ If valid, complete the task
            mark_task_as_completed(task, current_user=request.user)
            return {
                "success": True,
                "message": f"✅ Verified meeting `{meeting_id}` for client '{client.business_name}'. Task completed."
            }
        
        # 🚨 Meeting exists but is **not** in the allowed months
        return {
            "success": False,
            "message": f"⚠️ Meeting `{meeting_id}` is scheduled on {meeting.date.strftime('%d %B %Y')}, which is **not** in the current or next month."
        }
        
    def _check_schedule_meeting_created(self, task, request, meeting_id):
        """
        ✅ Ensure the client has the required number of **monthly** meetings.
        ✅ Allows scheduling meetings **for the current or next month**.
        ✅ Strictly validates using `meeting_id`.

        - New clients → Need **2** meetings in their first month.
        - Old clients → Need **1** meeting per month.
        - Prevents task completion if no valid meeting exists.
        """

        client = task.client
        current_date = datetime.now().date()
        current_year, current_month = current_date.year, current_date.month

        # 🔹 Get **next month & year** for scheduling flexibility
        next_month_date = current_date.replace(day=28) + timedelta(days=4)
        next_month, next_year = next_month_date.month, next_month_date.year

        # ✅ Step 1: Fetch the **specific meeting** using `meeting_id`
        try:
            meeting = Meeting.objects.get(id=meeting_id, client=client)
        except Meeting.DoesNotExist:
            return {
                "success": False,
                "message": f"⚠️ No meeting found with ID `{meeting_id}` for client '{client.business_name}'."
            }

        # ✅ Step 2: Check if the meeting is in **current or next month**
        if not ((meeting.date.year == current_year and meeting.date.month == current_month) or 
                (meeting.date.year == next_year and meeting.date.month == next_month)):
            return {
                "success": False,
                "message": f"⚠️ Meeting `{meeting_id}` is scheduled on {meeting.date.strftime('%d %B %Y')}, "
                        f"which is **not** in the current or next month."
            }

        # ✅ Step 3: Check **how many meetings the client has in the required months**
        past_meetings_exist = Meeting.objects.filter(client=client, date__lt=current_date).exists()
        required_meetings = 2 if not past_meetings_exist else 1  # New clients need 2, old clients need 1

        # ✅ Step 4: Check if enough meetings exist in the required months
        current_month_meetings = Meeting.objects.filter(client=client, date__year=current_year, date__month=current_month).count()
        next_month_meetings = Meeting.objects.filter(client=client, date__year=next_year, date__month=next_month).count()

        total_meetings = current_month_meetings + next_month_meetings

        if total_meetings < required_meetings:
            return {
                "success": False,
                "message": f"⚠️ Client '{client.business_name}' requires {required_meetings} meetings in {current_month}/{current_year} or {next_month}/{next_year}. "
                        f"Currently scheduled: {total_meetings}. Please schedule the required meetings before proceeding."
            }

        # ✅ Mark task as completed
        mark_task_as_completed(task, current_user=request.user)
        return {
            "success": True,
            "message": f"✅ Required meetings verified for client '{client.business_name}' in {current_month}/{current_year}. Task completed successfully."
        }
             
    def _check_calendar_resources(self, task, request, calender_id):
        """
        Check if all strategy resources are available in the ClientCalendarDate table for the client's 
        current month calendar. If all resources are completed, mark `strategy_completed = True` and complete the task.
        """
        client = task.client
        
        try:
            # ✅ Retrieve the client's calendar for the CURRENT MONTH using `created_at`
            client_calendar = ClientCalendar.objects.filter(
                client=client,
                id=calender_id
            ).first()

            # ✅ If no calendar exists for the current month, return error
            if not client_calendar:
                return {
                    "success": False,
                    "message": f"⚠️ No calendar found for {datetime.now().strftime('%B')} for client '{client.business_name}'. Please create a calendar before proceeding."
                }

            # ✅ Ensure all strategy resources are filled for the current month's calendar
            if not self._check_all_strategy_completed(client_calendar):
                return {
                    "success": False,
                    "message": f"⚠️ Not all strategy resources are filled for client '{client.business_name}' in {datetime.now().strftime('%B')}. Please complete all resources before proceeding."
                }

            # ✅ If everything is complete, update the calendar as `strategy_completed`
            if not client_calendar.strategy_completed:
                print(f"✅ Marking strategy as completed for {datetime.now().strftime('%B')}.")
                client_calendar.strategy_completed = True
                client_calendar.save()

            # ✅ Now mark the task as completed and proceed
            mark_task_as_completed(task, current_user=request.user)

            return {
                "success": True,
                "message": f"✅ All strategy resources are completed for client '{client.business_name}' in {datetime.now().strftime('%B')}, and the task has been forwarded to the next step."
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"⚠️ Error occurred while checking calendar: {str(e)}"
            }

    def _check_all_strategy_completed(self, calendar):
        """
        Ensure all strategy resources are filled in ClientCalendarDate for the given calendar (current month).
        """
        dates = ClientCalendarDate.objects.filter(calendar=calendar)

        # ✅ Check if 'resource' is filled for all rows in the calendar
        missing_resources = [date.date for date in dates if not date.resource or not date.resource.strip()]

        # ✅ If any resources are missing, return False and log the missing dates
        if missing_resources:
            print(f"⚠️ Strategy resources are missing for the following dates: {missing_resources}")
            return False

        # ✅ All dates have their strategy resources completed
        return True

    def _check_content_availability(self, task, request, calendar_id):
        """
        Ensure that all required content fields are present in the client's current month's calendar.
        If all required content is filled, mark the task as completed.
        """
        client = task.client

        try:
            # ✅ Get the client's calendar for the current month
            calendar = ClientCalendar.objects.filter(
                client=client,
                id=calendar_id
            ).first()

            # ✅ If no calendar exists, return error
            if not calendar:
                return {
                    "success": False,
                    "message": f"⚠️ No calendar found for {datetime.now().strftime('%B')} for client '{client.business_name}'. Please create a calendar before proceeding."
                }

            # Ensure all required content fields are completely filled for all calendar dates
            missing_dates = self._get_dates_with_missing_content(calendar)

            if missing_dates:
                return {
                    "success": False,
                    "message": f"⚠️ Content is missing in the following dates for client '{client.business_name}': {', '.join(missing_dates)}. Please fill all required fields before proceeding."
                }

            # ✅ Mark the task as completed and forward to the next step
            mark_task_as_completed(task, current_user=request.user)

            return {
                "success": True,
                "message": f"✅ All required content fields are filled for client '{client.business_name}' in {datetime.now().strftime('%B')}. Task completed and forwarded."
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"⚠️ Error occurred while checking content availability: {str(e)}"
            }

    def _get_dates_with_missing_content(self, calendar):
        """
        Check if any required content fields are missing for any date in the calendar.
        Returns a list of dates with missing content.
        """
        required_fields = ['tagline', 'caption', 'hashtags', 'e_hooks', 'creatives_text']
        dates = ClientCalendarDate.objects.filter(calendar=calendar)

        missing_dates = []

        for date in dates:
            # Treat `None` as empty
            if any(getattr(date, field) in [None, '', 'null'] for field in required_fields):
                missing_dates.append(date.date)  # Collect missing date names

        return missing_dates  # Return list of dates with missing content 

    # def _check_creatives_design_task(self, task, request, calendar_id):
        """
        Ensure **all creatives** are uploaded for the specified **calendar ID** before completing the task.
        """
        client = task.client

        try:
            # ✅ Retrieve **only one** ClientCalendar object using `calendar_id`
            client_calendar = ClientCalendar.objects.filter(
                client=client,
                id=calendar_id
            ).first()

            if not client_calendar:
                return {
                    "success": False,
                    "message": f"⚠️ No calendar found with ID `{calendar_id}` for client '{client.business_name}'."
                }

            # ✅ Check for missing creatives
            missing_creatives_dates = self._get_dates_with_missing_creatives(client_calendar)

            if not missing_creatives_dates:
                return {
                    "success": False,
                    "message": f"⚠️ Creatives are missing for the following dates in calendar `{calendar_id}` for client '{client.business_name}': "
                            f"{', '.join(missing_creatives_dates)}. Please upload creatives before proceeding."
                }

            # ✅ Ensure **all** creatives are actually uploaded before marking as complete
            if self._check_all_creatives_completed(client_calendar):
                return {
                    "success": True,
                    "message": f"⚠️ Not all creatives are completed for client '{client.business_name}' in calendar `{calendar_id}`. "
                            f"Please verify all creatives are uploaded before proceeding."
                }

            # Mark creatives as completed **only if everything is verified**
            if not client_calendar.creatives_completed:
                print(f"Marking creatives as completed for calendar `{calendar_id}`.")
                client_calendar.creatives_completed = True
                client_calendar.save()

            #  Now mark the task as completed and proceed
            mark_task_as_completed(task, current_user=request.user)

            return {
                "success": True,
                "message": f" All creatives are completed for client '{client.business_name}' in calendar `{calendar_id}`. Task completed successfully."
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"⚠️ Error occurred while checking creatives: {str(e)}"
            }

    def _check_creatives_design_task(self, task, request, calendar_id):
        client = task.client
        try:
            client_calendar = ClientCalendar.objects.filter(
                client=client,
                id=calendar_id
            ).first()

            if not client_calendar:
                return {
                    "success": False,
                    "message": f"⚠️ No calendar found with ID `{calendar_id}` for client '{client.business_name}'."
                }

            # ✅ Check for missing creatives (FIXED: Inverted condition)
            missing_creatives_dates = self._get_dates_with_missing_creatives(client_calendar)

            # SHOULD RETURN ERROR IF THERE ARE MISSING DATES
            if missing_creatives_dates:  # FIXED: Check for non-empty list
                return {
                    "success": False,
                    "message": f"⚠️ Creatives are missing for the following dates in calendar `{calendar_id}`: "
                            f"{', '.join(missing_creatives_dates)}"
                }

            # ✅ Ensure all creatives are uploaded (FIXED: Inverted logic)
            if not self._check_all_creatives_completed(client_calendar):
                return {
                    "success": False,
                    "message": f"⚠️ Creative verification failed for calendar `{calendar_id}`"
                }

            # Mark creatives as completed if needed
            if not client_calendar.creatives_completed:
                print(f"Marking creatives as completed for calendar `{calendar_id}`.")
                client_calendar.creatives_completed = True
                client_calendar.save()

            mark_task_as_completed(task, current_user=request.user)

            return {
                "success": True,
                "message": f"All creatives completed for client '{client.business_name}'!"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"⚠️ Error checking creatives: {str(e)}"
            }


    def _get_dates_with_missing_creatives(self, calendar):
        """
         Check if any dates in the calendar are missing creatives.
        - If creatives are missing, return a **list of dates**.
        - Otherwise, return an **empty list**.
        """
        #  Retrieve only the dates linked to **this specific calendar**
        dates = ClientCalendarDate.objects.filter(calendar=calendar)

        missing_dates = []

        for date in dates:
            #  Ensure `creatives` field is not empty, null, or just whitespace
            if not date.creatives or str(date.creatives).strip() in ['', 'null', 'None']:
                missing_dates.append(date.date)

        return missing_dates  #  Return the list of dates with missing creatives

    def _check_all_creatives_completed(self, calendar):
        """
        Ensure **all** dates in the client's calendar have their creatives uploaded.
        - If **any** creatives are missing, return `False`.
        """
        #  Retrieve only the dates linked to **this specific calendar**
        dates = ClientCalendarDate.objects.filter(calendar=calendar)

        for date in dates:
            if not date.creatives or str(date.creatives).strip() in ['', 'null', 'None']:
                return False  # 🚨 At least one date is missing creatives

        return True  #  All creatives are uploaded

    def _handle_approve_content_by_marketing_manager(self, task, request, calendar_id):
        """
        Handle the approval of content by the marketing manager.
        """
        client = task.client
        try:
            # Retrieve the client's calendar
            client_calendar = ClientCalendar.objects.get(client=client, id=calendar_id)

            # Get the status from the request
            status = request.data.get('status')  # Expecting 'status' in the request data
            if not status:
                return {"success": False, "message": "The 'status' field is required for updating the task."}

            # Update status and perform corresponding actions
            if status == 'approve':
                # Ensure all content is approved before proceeding
                if not self._check_all_content_approved_internal_status(client_calendar):
                    return {
                        "success": False,
                        "message": "Not all content fields in the calendar dates are approved. Please approve all content before proceeding."
                    }
                # Update status and save
                client_calendar.mm_content_completed = 'approved'
                client_calendar.save()
                # Mark task as completed and proceed to the next step
                mark_task_as_completed(task, current_user=request.user)
                return {"success": True, "message": "Content approved and task completed successfully."}

            elif status == 'changes_required':
         # ✅ Update status in the ClientCalendar model
                client_calendar.mm_content_completed = 'changes_required'
                client_calendar.save()

                # ✅ Determine the previous step and find the content writer
                previous_step = 'content_writing'
                previous_user = client.team.memberships.filter(user__role='content_writer').first()

                if previous_user:
                    # ✅ Mark the current task as completed (since it was rejected)
                    mark_task_as_completed(task, current_user=request.user)

                    # ✅ Create a new task for the content writer
                    new_task = create_task(client, previous_step, previous_user.user)

                    # ✅ Send real-time notification to the content writer
                    notification_message = f"⚠️ Content approval requires changes for client '{client.business_name}'. The task has been reassigned to you."
                    send_task_notification(
                        recipient=previous_user.user,  # Send to content writer
                        sender=request.user,  # The person rejecting the task
                        message=notification_message,
                        task=new_task,
                        notification_type="task_reassigned"
                    )

                    return {
                        "success": False,
                        "message": f"⚠️ Content approval requires changes. Task has been reassigned to the content writer and they have been notified."
                    }

                else:
                    return {
                        "success": False,
                        "message": "⚠️ No content writer found in the team. Unable to reassign the task for changes required."
                    }


            elif status == 'declined':
                # Update status and stop the workflow
                client_calendar.mm_content_completed = 'declined'
                client_calendar.save()
                return {
                    "success": False,
                    "message": f"Content approval for client '{client.business_name}' has been declined. Workflow will not proceed further."
                }

            else:
                return {
                    "success": False,
                    "message": f"Invalid status '{status}' provided. Allowed statuses are: 'approve', 'changes_required', or 'declined'."
                }

        except ClientCalendar.DoesNotExist:
            return {
                "success": False,
                "message": f"No calendar found for client '{client.business_name}'. Please create a calendar before proceeding."
            }

    def _check_all_content_approved_internal_status(self, calendar):
        """
        Check if all calendar dates have 'content_approval' set to 'approve' in internal_status.
        """
        dates = ClientCalendarDate.objects.filter(calendar=calendar)

        incomplete_dates = []
        
        for date in dates:
            internal_status = date.internal_status  # Get the stored internal_status dictionary

            # 🔍 Ensure internal_status is a dictionary
            if not isinstance(internal_status, dict):
                print(f"⚠️ Invalid internal_status format for date {date.date}. Expected dict but got {type(internal_status).__name__}.")
                incomplete_dates.append(date.date)
                continue  # Skip this date since it's in the wrong format

            # 🔍 **Ensure `content_approval` exists and is marked 'approve'**
            if "content_approval" not in internal_status or internal_status.get("content_approval") != True:
                incomplete_dates.append(date.date)

        # 🚨 If any dates are missing `content_approval`, return False and log the missing dates
        if incomplete_dates:
            print(f"⚠️ Content approval is missing for the following dates: {', '.join(map(str, incomplete_dates))}")
            return False  

        return True  # ✅ All required approvals exist 

    def _handle_approve_content_by_account_manager(self, task, request, calendar_id):
        """
        Handle the approval of content by the account manager.
        """
        client = task.client
        try:
            # Retrieve the client's calendar
            client_calendar = ClientCalendar.objects.get(client=client, id=calendar_id)

            # Get the status from the request
            status = request.data.get('status')  # Expecting 'status' in the request data
            if not status:
                return {"success": False, "message": "The 'status' field is required for updating the task."}

            # Handle 'approve' status
            if status == 'approve':
                # Ensure all client-approved content statuses are valid
                if not self._check_all_content_approved_client_approval(client_calendar):
                    return {
                        "success": False,
                        "message": "Not all content fields in the calendar dates are approved by the client. Please approve all content before proceeding."
                    }
                # Update status and save
                client_calendar.acc_content_completed = 'approved'
                client_calendar.save()

                # Mark task as completed and proceed to the next step
                mark_task_as_completed(task, current_user=request.user)
                return {"success": True, "message": "Content approved and task completed successfully."}

            # Handle 'changes_required' status
            elif status == 'changes_required':
                #  Update status in the ClientCalendar model
                client_calendar.acc_content_completed = 'changes_required'
                client_calendar.save()

                #  Determine the previous step and find the marketing manager
                previous_step = 'approve_content_by_marketing_manager'
                previous_user = client.team.memberships.filter(user__role='marketing_manager').first()

                if previous_user:
                    # Mark the current task as completed
                    mark_task_as_completed(task, current_user=request.user)

                    #  Create a new task for the marketing manager
                    new_task = create_task(client, previous_step, previous_user.user)

                    #  Send real-time notification to the marketing manager
                    notification_message = f"⚠️ Content approval requires changes for client '{client.business_name}'. The task has been reassigned to you."
                    send_task_notification(
                        recipient=previous_user.user,  # Send to marketing manager
                        sender=request.user,  # The person rejecting the task
                        message=notification_message,
                        task=new_task,
                        notification_type="task_reassigned"
                    )

                    return {
                        "success": False,
                        "message": f"⚠️ Content approval requires changes. Task has been reassigned to the marketing manager and they have been notified."
                    }

                else:
                    return {
                        "success": False,
                        "message": "⚠️ No marketing manager found in the team. Unable to reassign the task for changes required."
                    }


            # Handle 'declined' status
            elif status == 'declined':
                # Update status and stop the workflow
                client_calendar.acc_content_completed = 'declined'
                client_calendar.save()
                return {
                    "success": False,
                    "message": f"Content approval for client '{client.business_name}' has been declined. Workflow will not proceed further."
                }

            # Handle invalid status
            else:
                return {
                    "success": False,
                    "message": f"Invalid status '{status}' provided. Allowed statuses are: 'approve', 'changes_required', or 'declined'."
                }

        except ClientCalendar.DoesNotExist:
            return {
                "success": False,
                "message": f"No calendar found for client '{client.business_name}'. Please create a calendar before proceeding."
            }

    def _check_all_content_approved_client_approval(self, calendar):
        """
        Check if all content fields are approved in the client_approval JSON field.
        """
        dates = ClientCalendarDate.objects.filter(calendar=calendar)
        incomplete_dates = [
            date.date for date in dates
            if date.client_approval.get('content_approval') != True
        ]

        if incomplete_dates:
            print(f"Content approval missing in client_approval for the following dates: {', '.join(map(str, incomplete_dates))}")
            return False

        return True

    def _handle_approve_creatives_by_marketing_manager(self, task, request, calendar_id):
        """
        Handle the approval of creatives by the marketing manager.
        """
        client = task.client
        try:
            # Retrieve the client's calendar
            client_calendar = ClientCalendar.objects.get(client=client, id=calendar_id)

            # Get the status from the request
            status = request.data.get('status')  # Expecting 'status' in the request data
            if not status:
                return {"success": False, "message": "The 'status' field is required for updating the task."}

            # Handle 'approve' status
            if status == 'approve':
                # Ensure all creatives are approved before proceeding
                if not self._check_all_creatives_approved_internal_status(client_calendar):
                    return {
                        "success": False,
                        "message": "Not all creatives fields in the calendar dates are approved. Please approve all creatives before proceeding."
                    }
                # Update status and save
                client_calendar.mm_creative_completed = 'approved'
                client_calendar.save()

                # Mark task as completed and proceed to the next step
                mark_task_as_completed(task, current_user=request.user)
                return {"success": True, "message": "Creatives approved and task completed successfully."}

            # Handle 'changes_required' status
            elif status == 'changes_required':
                # Update status
                client_calendar.mm_creative_completed = 'changes_required'
                client_calendar.save()

                # Determine the previous step and reassign task
                previous_step = 'creatives_design'
                previous_user = client.team.memberships.filter(user__role='graphics_designer').first()
                if previous_user:
                    mark_task_as_completed(task, current_user=request.user)
                    create_task(client, previous_step, previous_user.user)
                    return {
                        "success": False,
                        "message": f"Creatives approval requires changes. Task has been reassigned to the graphics designer."
                    }
                else:
                    return {
                        "success": False,
                        "message": "No graphics designer found in the team. Unable to reassign the task for changes required."
                    }

            # Handle 'declined' status
            elif status == 'declined':
                # Update status and stop the workflow
                client_calendar.mm_creative_completed = 'declined'
                client_calendar.save()
                return {
                    "success": False,
                    "message": f"Creatives approval for client '{client.business_name}' has been declined. Workflow will not proceed further."
                }

            # Handle invalid status
            else:
                return {
                    "success": False,
                    "message": f"Invalid status '{status}' provided. Allowed statuses are: 'approve', 'changes_required', or 'declined'."
                }

        except ClientCalendar.DoesNotExist:
            return {
                "success": False,
                "message": f"No calendar found for client '{client.business_name}'. Please create a calendar before proceeding."
            }

    def _check_all_creatives_approved_internal_status(self, calendar):
        """
        Check if all calendar dates have their 'creatives_approval' in internal_status set to 'approve'.
        """
        dates = ClientCalendarDate.objects.filter(calendar=calendar)
        incomplete_dates = [
            date.date for date in dates
            if date.internal_status.get('creatives_approval') != True
        ]

        if incomplete_dates:
            print(f"Creatives approval is missing for the following dates: {', '.join(map(str, incomplete_dates))}")
            return False

        return True

    def _handle_approve_creatives_by_account_manager(self, task, request, calendar_id):
        """
        Handle the approval of creatives by the account manager.
        """
        client = task.client 
        try:
            # Retrieve the client's calendar
            client_calendar = ClientCalendar.objects.get(client=client, id=calendar_id)

            # Get the status from the request
            status = request.data.get('status')  # Expecting 'status' in the request data
            if not status:
                return {"success": False, "message": "The 'status' field is required for updating the task."}

            # Handle 'approve' status
            if status == 'approve':
                # Ensure all client-approved creatives are valid
                if not self._check_all_creatives_approved_client_approval(client_calendar):
                    return {
                        "success": False,
                        "message": "Not all creatives fields in the calendar dates are approved by the client. Please approve all creatives before proceeding."
                    }
                # Update status and save
                client_calendar.acc_creative_completed = 'approved'
                client_calendar.save()

                # Mark task as completed and proceed to the next step
                mark_task_as_completed(task, current_user=request.user)
                return {"success": True, "message": "Creatives approved and task completed successfully."}

            # Handle 'changes_required' status
            elif status == 'changes_required':
                # Update status
                client_calendar.acc_creative_completed = 'changes_required'
                client_calendar.save()

                # Determine the previous step and reassign task
                previous_step = 'approve_creatives_by_marketing_manager'
                previous_user = client.team.memberships.filter(user__role='marketing_manager').first()
                if previous_user:
                    mark_task_as_completed(task, current_user=request.user)
                    create_task(client, previous_step, previous_user.user)
                    return {
                        "success": False,
                        "message": f"Creatives approval requires changes. Task has been sent back to the marketing manager."
                    }
                else:
                    return {
                        "success": False,
                        "message": "No marketing manager found in the team. Unable to reassign the task for changes required."
                    }

            # Handle 'declined' status
            elif status == 'declined':
                # Update status and stop the workflow
                client_calendar.acc_creative_completed = 'declined'
                client_calendar.save()
                return {
                    "success": False,
                    "message": f"Creatives approval for client '{client.business_name}' has been declined. Workflow will not proceed further."
                }

            # Handle invalid status
            else:
                return {
                    "success": False,
                    "message": f"Invalid status '{status}' provided. Allowed statuses are: 'approve', 'changes_required', or 'declined'."
                }

        except ClientCalendar.DoesNotExist:
            return {
                "success": False,
                "message": f"No calendar found for client '{client.business_name}'. Please create a calendar before proceeding."
            }

    def _check_all_creatives_approved_client_approval(self, client_calendar):
        """
        Check if all creatives fields are approved in the client_approval JSON field.
        """
        dates = ClientCalendarDate.objects.filter(calendar=client_calendar)
        incomplete_dates = [
            date.date for date in dates
            if date.client_approval.get('creatives_approval') != True
        ]

        if incomplete_dates:
            print(f"Creatives approval missing in client_approval for the following dates: {', '.join(map(str, incomplete_dates))}")
            return False

        return True

    def _check_invoice_verification(self, task, request, invoice_id):
        """
        Check if the account manager has verified the submitted invoice for the latest month.
        """
        client = task.client

        # Get the current date and calculate the latest month and year
        current_date = now()
        latest_month = current_date.month
        latest_year = current_date.year

        try:
            # Filter invoices for the specific client, latest month, and year,
            # ordering them by created_at descending so that the most recent is checked.
            invoice = ClientInvoices.objects.filter(
                client=client,
                id=invoice_id
            ).order_by('-created_at').first()

            if not invoice:
                return {
                    "success": False,
                    "message": f"No invoice found for {latest_month}/{latest_year} for client '{client.business_name}'."
                }

            # Check the submission_status.
            # (Adjust the condition as needed for your business logic.)
            # For example, if the invoice is still 'unpaid', it means it hasn't been verified yet.
            if invoice.submission_status != 'unpaid':
                return {
                    "success": False,
                    "message": f"The submitted invoice for {latest_month}/{latest_year} has not been verified by the account manager."
                }

            # Invoice is verified (i.e. it passes the check),
            # so mark the task as completed and proceed.
            mark_task_as_completed(task, current_user=request.user)
            return {"success": True, "message": f"Invoice for {latest_month}/{latest_year} verified successfully."}

        except Exception as e:
            # Handle any unexpected errors
            return {"success": False, "message": f"An error occurred while checking the invoice: {str(e)}"}

    def _check_latest_month_invoice_submission(self, task, request, invoice_id):
        """
        Checks if an invoice has been uploaded for the latest month before completing a task.
        """
        client = task.client

        try:
            # Get the current date
            current_date = now()

            # Get the start of the current month
            start_of_month = current_date.replace(day=1)

            # Filter invoices for this client created in the current month
            latest_invoice = ClientInvoices.objects.filter(
                client=client,
                id=invoice_id
            ).first()

            # Check if an invoice exists
            if latest_invoice and latest_invoice.invoice:
                # Mark the task as completed and proceed to the next step
                mark_task_as_completed(task, current_user=request.user)
                return {
                    "success": True,
                    "message": f"Invoice for the latest month has been submitted successfully for client '{client.business_name}'."
                }
            else:
                return {
                    "success": False,
                    "message": f"No invoice uploaded for the latest month for client '{client.business_name}'. Please upload the invoice before completing this task."
                }

        except Exception as e:
            # Handle unexpected errors
            return {
                "success": False,
                "message": f"An error occurred while checking the invoice submission: {str(e)}"
            }
 
    def _check_payment_status(self, task, request, invoice_id):
        """
        Check the payment status of the client's invoice.
        Completes the task only if the payment status is 'paid' and forwards to the next step.
        """
        client = task.client

        try:
            # Get the most recent invoice for the client
            latest_invoice = ClientInvoices.objects.filter(
                client=client,
                id=invoice_id
            ).first()

            if not latest_invoice:
                return {
                    "success": False,
                    "message": f"No invoice found for client '{client.business_name}'. Please ensure an invoice is submitted before proceeding."
                }

            # Check if the payment status is 'paid'
            if latest_invoice.submission_status == 'paid':
                # Mark the current task as completed and proceed to the next step
                mark_task_as_completed(task, current_user=request.user)

                # Optionally, log or return the successful action
                return {"success": True, "message": "Payment confirmed and task forwarded successfully."}
            else:
                return {
                    "success": False,
                    "message": f"Payment status for the latest invoice of client '{client.business_name}' is '{latest_invoice.submission_status}'. Task cannot be completed until the payment is marked as 'paid'."
                }

        except Exception as e:
            # Handle unexpected errors
            return {
                "success": False,
                "message": f"An error occurred while checking payment status: {str(e)}"
            }

    def _update_smo_flag(self, task, request, calender_id):
        """
        Update the 'smo_completed' field in the ClientCalendar for the client's current month.
        """
        client = task.client
        try:
            # Determine the current month and year
            current_date = task.created_at
            
            # Retrieve or create the client's calendar for the current month
            client_calendar, created = ClientCalendar.objects.get_or_create(
                client=client,
                id=calender_id
            )

            # Update the 'smo_completed' field
            client_calendar.smo_completed = True
            client_calendar.save()

            # Mark task as completed and proceed to the next step
            mark_task_as_completed(task, current_user=request.user)

            return {"success": True, "message": "SMO task completed and calendar updated successfully."}

        except Exception as e:
            return {
                "success": False,
                 "message": f"An error occurred while updating the calendar for client '{client.business_name}': {str(e)}"
            }
    
class TaskListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        # Get the client_id from URL parameters
        client_id = self.kwargs.get('client_id')
        if client_id:
            # Filter tasks by client_id
            return Task.objects.filter(client_id=client_id, is_completed=False)
        # Return an empty queryset if no client_id is provided
        return Task.objects.none()

class UserAssignedTaskListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MyTaskSerializer

    def get_queryset(self):
        # Fetch tasks assigned to the currently authenticated user and filter by completion status
        return Task.objects.filter(assigned_to=self.request.user, is_completed=False).select_related('client')

class UserCustomTaskListView(APIView):
    """Retrieve all custom tasks assigned to the logged-in user."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        #  Retrieve tasks assigned to the current user
        user_tasks = CustomTask.objects.filter(assign_to_id=request.user)
        serialized_tasks = CustomTaskSerializer(user_tasks, many=True, context={"request": request}).data

        return Response({"tasks": serialized_tasks}, status=status.HTTP_200_OK)

class UpdateCustomTaskStatusView(APIView):
    """Allow users to update the task_status and file of their own assigned tasks."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(CustomTask, id=task_id)

        # Allow either the assigned user or the task creator (Account Manager)
        if task.assign_to_id != request.user and task.client_id.account_manager != request.user:
            return Response({"error": "You are not authorized to update this task."}, status=status.HTTP_403_FORBIDDEN)

        # Store the old file path BEFORE replacing the file
        old_file_path = task.custom_task_file

        # Handle new file upload
        new_file = request.FILES.get("task_file")
        if new_file:
            tmp_path = None
            try:
                # Save upload to a temp file
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    for chunk in new_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                path_in_bucket = f"task_files/{new_file.name}"

                # Try upload; on 409 overwrite via update()
                try:
                    storage.upload(
                        file=tmp_path,
                        path=path_in_bucket,
                        file_options={"content-type": new_file.content_type}
                    )
                except StorageApiError as exc:
                    raw = exc.args[0] if exc.args else {}
                    if isinstance(raw, dict) and raw.get("statusCode") == 409:
                        storage.update(
                            file=tmp_path,
                            path=path_in_bucket,
                            file_options={"content-type": new_file.content_type}
                        )
                    else:
                        msg = raw.get("message", str(exc)) if isinstance(raw, dict) else str(exc)
                        return Response({"error": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Update task with new file path
                task.custom_task_file = path_in_bucket
            finally:
                # Clean up temp file
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        # Update task status if provided
        new_status = request.data.get("task_status")
        if new_status is not None:
            task.task_status = new_status

        task.save()

        # Delete old file after saving the new one
        if old_file_path:
            try:
                storage.remove([old_file_path])
            except Exception as e:
                print(f"❌ Failed to delete old task file: {e}")

        # Notify Account Manager if task completed
        if new_status is True:
            client = task.client_id
            account_manager = client.account_manager
            if account_manager:
                notification_message = (
                    f"Task '{task.task_name}' assigned to {request.user.get_full_name()} for client {client.business_name} has been completed."
                )
                send_task_notification(
                    recipient=account_manager,
                    sender=request.user,
                    message=notification_message,
                    task=task,
                    notification_type="task_completed"
                )

        return Response({
            "message": "Task updated successfully",
            "task": CustomTaskSerializer(task, context={"request": request}).data
        }, status=status.HTTP_200_OK)

