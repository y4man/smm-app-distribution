# Django imports
from django.shortcuts import  get_object_or_404
from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings
from django.urls import reverse
from django.core.files.storage import default_storage

# DRF (Django REST Framework) imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied

# Python standard library imports
import random
import string
import os
import tempfile
from urllib.parse import urlparse

# Project-specific imports
from pro_app import storage
from storage3.exceptions import StorageApiError
from account.models import CustomUser
from pro_app.utils import send_task_notification
from . import serializers
from . import models
from user.models import UserOTP
from plan.models import Plans
from task.models import Task, CustomTask
from team.models import Team, TeamMembership
from task.serializers import TaskSerializer, CustomTaskSerializer
from calender.models import ClientCalendar
from user.serializers import UserSerializer
from client.models import Clients
from pro_app.permissions import IsMarketingDirector


# Client Signup
class UserSignupView(APIView):
    """
     Allows new users to sign up with a fixed role ('user').
     Associates users with an account manager based on `agency_slug`.
     Accepts password input from the user.
     Sends an OTP for verification.
     Users can log in even if OTP is not entered.
    """
    permission_classes = [AllowAny]
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))

    def post(self, request, *args, **kwargs):
        data = request.data
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        password = data.get('password')  #  Accept password from user
        agency_slug = data.get('agency_slug')

        # 🔹 Check if user with this email already exists
        if CustomUser.objects.filter(email=email).exists():
            return Response({"message": " A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Find the **Account Manager** linked to the `agency_name`
        try:
            agency = CustomUser.objects.get(agency_slug=agency_slug, role='account_manager')
            account_manager_id = agency.id  # Extract Account Manager ID
        except CustomUser.DoesNotExist:
            return Response({"message": " No valid agency found for the provided agency slug."}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Auto-generate a unique username from the email
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # 🔹 Generate an OTP
        otp_code = self.generate_otp()

        # 🔹 Create a new user with a fixed role 'user'
        user = CustomUser.objects.create(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role='user',  # Fixed role
            acc_mngr_id=account_manager_id,  # Associate with the Account Manager
            is_active=True  # User is active but must verify OTP
        )
        user.set_password(password)  #  Use the provided password
        user.save()

        # 🔹 Store OTP in the **UserOTP** model (not in CustomUser)
        UserOTP.objects.create(user=user, otp=otp_code, is_verified=False)

        # 🔹 Send OTP via Email
        subject = "Verify Your Account - OTP Code"
        body = (
            f"Hi {first_name},\n\n"
            f"Your OTP for verification is: {otp_code}\n\n"
            f"Please enter this OTP to verify your account.\n\n"
            f"Best regards,\nSMMEXPERTS Team"
        )

        try:
            send_mail(subject, body, settings.EMAIL_HOST_USER, [email])
            return Response(
                {
                    "message": " User registered successfully. OTP sent for verification.",
                    "username": username,
                    "otp": otp_code  # For testing only, remove this in production
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            user.delete()  # If email fails, delete the user
            return Response({"message": f" Failed to send OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ClientPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id, *args, **kwargs):
        """
        Retrieve the plan for a specific client and fetch detailed plan data based on plan type.
        """
        # Retrieve the client
        client = get_object_or_404(models.Clients, id=client_id)

        # Get the client's account manager
        account_manager = client.account_manager  # Ensure the account manager is fetched first
        if not account_manager:
            return Response({"error": "Client does not have an assigned account manager."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the client's plan
        client_plan = models.ClientsPlan.objects.filter(client=client).first()
        if not client_plan:
            return Response({"error": "No plan found for the specified client."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch the plan associated with the account manager and the plan type
        plan_type = client_plan.plan_type
        plan = Plans.objects.filter(account_managers__id=account_manager.id).first()  # Filter plans associated with the account manager

        if not plan:
            return Response({"error": f"No {plan_type} plan found for the client's account manager."}, status=status.HTTP_404_NOT_FOUND)

         # Add detailed plan data into the client_plan object
        client_plan_data = serializers.ClientsPlanSerializer(client_plan).data
        if plan_type.lower() == "standard":
            client_plan_data["plan_attributes"] = plan.standard_attributes
            client_plan_data["plan_net_price"] = plan.standard_netprice
        elif plan_type.lower() == "advanced":
            client_plan_data["plan_attributes"] = plan.advanced_attributes
            client_plan_data["plan_net_price"] = plan.advanced_netprice
        else:
            return Response({"error": f"Unknown plan type: {plan_type}"}, status=status.HTTP_400_BAD_REQUEST)

        # Return the response with the modified client_plan object
        return Response(client_plan_data, status=status.HTTP_200_OK)

    def post(self, request, client_id, *args, **kwargs):
        """
        Create a new plan for a specific client.
        """

        if self.request.user.role != 'account_manager':
            raise PermissionDenied("Only Account Managers can create a client plan.")

        client = get_object_or_404(models.Clients, id=client_id)

        # Check if the client already has a plan
        if models.ClientsPlan.objects.filter(client=client).exists():
            return Response({"error": "Client already has an existing plan."}, status=status.HTTP_400_BAD_REQUEST)

        # Proceed to create the new plan
        serializer = serializers.ClientsPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(client=client)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, client_id, *args, **kwargs):
        """
        Update the plan for a specific client.
        """
        if self.request.user.role != 'account_manager':
           raise PermissionDenied("Only Account Managers can create a client plan.")

        client = get_object_or_404(models.Clients, id=client_id)
        plan = models.ClientsPlan.objects.filter(client=client).first()

        if not plan:
            return Response({"error": "No plan found for the specified client."}, status=status.HTTP_404_NOT_FOUND)

        # Allow partial updates
        serializer = serializers.ClientsPlanSerializer(plan, data=request.data, partial=True)

        if serializer.is_valid():
            updated_data = serializer.validated_data

            # Merge JSON fields like 'attributes', 'platforms', and 'add_ons'
            if "attributes" in updated_data:
                current_attributes = plan.attributes or {}
                current_attributes.update(updated_data["attributes"])
                updated_data["attributes"] = current_attributes

            if "platforms" in updated_data:
                current_platforms = plan.platforms or {}
                current_platforms.update(updated_data["platforms"])
                updated_data["platforms"] = current_platforms

            # if "add_ons" in updated_data:
            #     current_add_ons = plan.add_ons or {}
            #     current_add_ons.update(updated_data["add_ons"])
            #     updated_data["add_ons"] = current_add_ons

            # Save the updated plan data
            serializer.save(**updated_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ClientWebDevDataListCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access
    serializer_classes = {
        'client': serializers.ClientSerializer,
        'webdev_data': serializers.ClientSerializer  # Update if a different serializer is used
    }

    def get(self, request, *args, **kwargs):
        """List all clients or fetch specific client's web development data"""
        client_id = self.kwargs.get('id', None)

        # ✅ If role is "user", return only the client linked to them
        if request.user.role == "user":
            client = models.Clients.objects.filter(created_by=request.user).first()
            if not client:
                return Response({"error": "⚠️ No client found linked to this user."}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = self.serializer_classes['client'](client)
            return Response(serializer.data)

        # ✅ If role is "account_manager", return the list of clients
        elif request.user.role != "user":
            clients = models.Clients.objects.all()
            serializer = self.serializer_classes['client'](clients, many=True)
            return Response(serializer.data)

        # 🚫 Other roles cannot access client data
        return Response({"error": "⚠️ You are not authorized to view this data."}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request, *args, **kwargs):
        """Create a new client and establish relationships"""

        client_id = self.kwargs.get('id', None)

        if client_id:
            # If a client ID is provided, create web development data for that client
            client = get_object_or_404(models.Clients, id=client_id)
            serializer = self.serializer_classes['webdev_data'](data=request.data)
            if serializer.is_valid():
                serializer.save(client=client)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # **Check if User Already Created a Client**
        if request.user.role == "user":
            existing_client = models.Clients.objects.filter(created_by=request.user).exists()
            if existing_client:
                return Response(
                    {"error": "⚠️ You have already created a client. Users can create only one client."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # **Create a new client**
        data = request.data.copy()
        account_manager_id = data.get('account_manager_id')

        # ✅ Check role and assign `account_manager_id`
        if request.user.role == "user":
            # Fetch `acc_mngr_id` from `CustomUser` model for the logged-in user
            if not request.user.acc_mngr_id:
                return Response(
                    {"error": "⚠️ You are not linked to any account manager. Contact support."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            account_manager_id = request.user.acc_mngr_id  # Use the assigned `acc_mngr_id`
        elif request.user.role == "account_manager":
            # If the user is an account manager, use their ID
            account_manager_id = request.user.id
        else:
            return Response(
                {"error": "⚠️ Only users and account managers can create clients."},
                status=status.HTTP_403_FORBIDDEN
            )

        # ✅ Validate the existence of the `account_manager_id`
        account_manager = get_object_or_404(CustomUser, id=account_manager_id, role='account_manager')

        # ✅ Ensure that `created_by` is the currently logged-in user
        data['created_by'] = request.user.id

        # ✅ Assign `account_manager` and `created_by`, then create client
        serializer = self.serializer_classes['client'](data=data)
        if serializer.is_valid():
            serializer.save(account_manager=account_manager, created_by=request.user)  # ✅ Store creator
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientWebDevDataDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_classes = {
        'client': serializers.ClientSerializer,
        'webdev_data': serializers.ClientSerializer
    }
    
    def check_permissions(self, request):
        """Ensure only account managers can update or delete"""
        if request.method in ['PUT', 'DELETE'] and request.user.role != 'account_manager':
            self.permission_denied(
                request,
                message="You do not have permission to perform this action.",
                code=status.HTTP_403_FORBIDDEN
            )
    def get(self, request, pk, *args, **kwargs):
        # Retrieve specific client or webdev data
        if kwargs.get('id') is None:
            # Retrieve a single client
            client = get_object_or_404(models.Clients, pk=pk)
            serializer = self.serializer_classes['client'](client)
            return Response(serializer.data)
        else:
            # Retrieve specific webdev data for a client
            webdev_data = get_object_or_404(models.ClientWebDevData, pk=pk)
            serializer = self.serializer_classes['webdev_data'](webdev_data)
            return Response(serializer.data)
   
    def put(self, request, pk, *args, **kwargs):
        self.check_permissions(request)  # Restrict to account managers
        # Update client or webdev data
        if kwargs.get('id') is None:
            # Update client
            client = get_object_or_404(models.Clients, pk=pk)
            serializer = self.serializer_classes['client'](client, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Update webdev data
            webdev_data = get_object_or_404(models.ClientWebDevData, pk=pk)
            serializer = self.serializer_classes['webdev_data'](webdev_data, data=request.data, partial=False)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   
    def delete(self, request, pk, *args, **kwargs):
        self.check_permissions(request)  # Restrict to account managers
        # Delete client or webdev data
        if kwargs.get('id') is None:
            # Delete client
            client = get_object_or_404(models.Clients, pk=pk)
            client.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # Delete webdev data
            webdev_data = get_object_or_404(models.ClientWebDevData, pk=pk)
            webdev_data.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        

class AssignClientToTeamView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsMarketingDirector]  # Ensure the user is authenticated
    queryset = models.Clients.objects.all()
    serializer_class = serializers.AssignClientToTeamSerializer

    def update(self, request, *args, **kwargs):
        # Check if the logged-in user has the "marketing_director" role
        if request.user.role.replace(' ', '_').lower() != 'marketing_director':
            return Response(
                {"error": "Only Marketing Director can assign a client to a team."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Proceed with team assignment if the user is a marketing director
        client = self.get_object()  # Get the client object based on the client ID (pk)
        team_id = request.data.get('team_id')

        # Validate the team_id
        if not team_id:
            return Response({"error": "Team ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            team = Team.objects.get(id=team_id)  # Fetch the team based on the team_id in the request data
        except Team.DoesNotExist:
            return Response({"error": "Team not found."}, status=status.HTTP_404_NOT_FOUND)

        # Assign the client to the team
        client.team = team
        client.save()

        serializer = self.get_serializer(client)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UpdateClientWorkflowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, client_id):
        client = get_object_or_404(models.Clients, id=client_id)
        task_type = request.data.get('task_type')
        assigned_to_id = request.data.get('assigned_to')


        if not task_type or not assigned_to_id:
            return Response({"error": "task_type and assigned_to are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assigned_user = CustomUser.objects.get(id=assigned_to_id)
        except CustomUser.DoesNotExist:
            return Response({"error": f"User with ID {assigned_to_id} does not exist."},
                    status=status.HTTP_400_BAD_REQUEST)
        # Update or create the task for the client
        task, created = Task.objects.update_or_create(
            client=client,
            task_type=task_type,
            defaults={'assigned_to_id': assigned_to_id, 'is_completed': False}
        )

        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    

class UploadProposalView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes     = (MultiPartParser, FormParser)

    def get(self, request, client_id, *args, **kwargs):
        client     = get_object_or_404(models.Clients, id=client_id)
        serializer = serializers.ClientProposalSerializer(client, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, client_id, *args, **kwargs):
        client = get_object_or_404(models.Clients, id=client_id)

        # 1) grab old key (path) if any
        old_key = client.proposal_pdf.name if client.proposal_pdf else None

        # 2) handle new upload
        new_file = request.FILES.get('proposal_pdf')
        if new_file:
            tmp_path = None
            try:
                # write to temp file
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    for chunk in new_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                path_in_bucket = f"proposals/{new_file.name}"

                # delete old
                if old_key:
                    try:
                        storage.remove([old_key])
                    except Exception:
                        pass

                # upload (or update on 409)
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
                        return Response({"proposal_pdf": [msg]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # store just the key
                client.proposal_pdf.name = path_in_bucket

            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        # 3) other field
        if 'proposal_approval_status' in request.data:
            client.proposal_approval_status = request.data['proposal_approval_status']

        client.save()
        serializer = serializers.ClientProposalSerializer(client, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, client_id, *args, **kwargs):
        client = get_object_or_404(models.Clients, id=client_id)

        # Delete the proposal file from Wasabi
        if client.proposal_pdf:
            try:
                parsed_url = urlparse(client.proposal_pdf.url)
                file_key = parsed_url.path.lstrip('/')
                default_storage.delete(file_key)
                print(f"Deleted proposal from Wasabi: {file_key}")
            except Exception as e:
                print(f"Failed to delete proposal: {e}")

            # Clear from DB
            client.proposal_pdf = None
            client.save()
            return Response({"message": "Proposal PDF deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        return Response({"error": "No proposal PDF found to delete."}, status=status.HTTP_404_NOT_FOUND)
    

class ClientInvoicesListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = serializers.ClientInvoicesSerializer
    parser_classes     = [MultiPartParser, FormParser]

    def get_queryset(self):
        client_id = self.kwargs['client_id']
        return models.ClientInvoices.objects.filter(client_id=client_id)

    def post(self, request, *args, **kwargs):
        client_id    = self.kwargs['client_id']
        client       = get_object_or_404(models.Clients, id=client_id)
        invoice_file = request.FILES.get('invoice')

        if not invoice_file:
            return Response(
                {"invoice": ["No file uploaded."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        tmp_path = None
        try:
            # 1) save upload to a temp file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                for chunk in invoice_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            path_in_bucket = f"invoices/{invoice_file.name}"

            # 2) try upload; on 409 overwrite via update()
            try:
                storage.upload(
                    file=tmp_path,
                    path=path_in_bucket,
                    file_options={"content-type": invoice_file.content_type}
                )
            except StorageApiError as exc:
                raw = exc.args[0] if exc.args else {}
                if isinstance(raw, dict) and raw.get("statusCode") == 409:
                    storage.update(
                        file=tmp_path,
                        path=path_in_bucket,
                        file_options={"content-type": invoice_file.content_type}
                    )
                else:
                    msg = raw.get("message", str(exc)) if isinstance(raw, dict) else str(exc)
                    return Response({"invoice": [msg]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            # always clean up temp file
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        # 3) store only the bucket path; serializer will build the full URL
        invoice = models.ClientInvoices.objects.create(
            client            = client,
            invoice           = path_in_bucket,             # <-- just the path!
            submission_status = 'wait_for_approval',
            billing_from      = request.data.get('billing_from'),
            billing_to        = request.data.get('billing_to'),
            payment_url       = request.data.get('payment_url'),
        )

        serializer = self.get_serializer(invoice, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _send_invoice_email(self, request, client, invoice, payment_url):
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        import smtplib

        account_manager = client.account_manager
        if not account_manager or not account_manager.email:
            print("❌ Account manager not found or missing email.")
            return

        if not invoice.invoice:
            print(f"❌ No invoice file uploaded for invoice #{invoice.id}")
            return

        try:
            approve_url = f"{request.build_absolute_uri(reverse('approve-invoice'))}?invoice_id={invoice.id}"
            reject_url = f"{request.build_absolute_uri(reverse('reject-invoice'))}?invoice_id={invoice.id}"
        except Exception as e:
            print(f"❌ Failed to build invoice action URLs: {e}")
            return

        subject = f"Invoice #{invoice.id} for {client.business_name}"
        body = f"""
        <html>
        <body>
            <p>Dear {account_manager.first_name},</p>
            <p>Please find attached the invoice for {client.business_name}.</p>
            <p>
                <a href='{approve_url}' style='background-color:green;color:white;padding:10px;text-decoration:none;'>Approve</a>
                <a href='{reject_url}' style='background-color:red;color:white;padding:10px;text-decoration:none;'>Reject</a>
            </p>
            {f"<p><strong>Payment URL:</strong> <a href='{payment_url}'>{payment_url}</a></p>" if payment_url else ""}
            <p>Best regards,<br>Your Team</p>
        </body>
        </html>
        """

        message = MIMEMultipart()
        message['From'] = 'danishkaleem@smmexperts.pro'
        message['To'] = account_manager.email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'html'))

        try:
            local_path = default_storage.path(invoice.invoice.name)
            with open(local_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(local_path)}')
                message.attach(part)
        except Exception as e:
            print(f"❌ Failed to attach invoice file: {e}")
            return

        try:
            smtp = smtplib.SMTP('smtp.titan.email', 465)
            smtp.starttls()
            smtp.login('danishkaleem@smmexperts.pro', 'Search$fs8@')
            smtp.sendmail(message['From'], message['To'], message.as_string())
            smtp.quit()
            print(f"✅ Invoice email sent to {account_manager.email}")
        except Exception as e:
            print(f"❌ Error sending email: {e}")

class ApproveInvoiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        invoice_id = request.GET.get('invoice_id')
        invoice = get_object_or_404(models.ClientInvoices, id=invoice_id)
        invoice.submission_status = 'unpaid'  # Update status to "unpaid"
        invoice.save()
        return HttpResponse("Invoice approved successfully.")

class RejectInvoiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        invoice_id = request.GET.get('invoice_id')
        invoice = get_object_or_404(models.ClientInvoices, id=invoice_id)
        invoice.submission_status = 'changes_required'  # Update status to "changes required"
        invoice.save()
        return HttpResponse("Invoice rejected.")

class ClientInvoicesRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = serializers.ClientInvoicesSerializer

    def get_queryset(self):
        client_id = self.kwargs['client_id']
        return models.ClientInvoices.objects.filter(client_id=client_id)

    def perform_destroy(self, instance):
        if instance.invoice:
            try:
                storage.remove([instance.invoice])
            except Exception:
                pass
        instance.delete()

    def update(self, request, *args, **kwargs):
        invoice = get_object_or_404(
            models.ClientInvoices,
            pk=kwargs['pk'],
            client_id=kwargs['client_id']
        )

        new_file = request.FILES.get('invoice')
        if new_file:
            # overwrite in-place at the old key
            try:
                new_key = storage.save_file_to_supabase(
                    uploaded_file=new_file,
                    folder="invoices",
                    target_key=invoice.invoice  # <-- important!
                )
            except Exception as exc:
                return Response(
                    {"invoice": [str(exc)]},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            invoice.invoice = new_key

        # update any other fields
        for fld in ['billing_from', 'billing_to', 'payment_url', 'submission_status']:
            if fld in request.data:
                setattr(invoice, fld, request.data[fld])

        invoice.save()
        return Response(self.get_serializer(invoice, context={'request': request}).data)


class ClientMonthlyReportsListCreateView(APIView):
    parser_classes     = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id, month_name, *args, **kwargs):
        client = get_object_or_404(models.Clients, id=client_id)
        try:
            calendar = ClientCalendar.objects.get(client=client, month_name=month_name)
        except ClientCalendar.DoesNotExist:
            return Response({"error": "No calendar found for that client & month."},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.ClientReportSerializer(calendar, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, client_id, month_name, *args, **kwargs):
        client = get_object_or_404(models.Clients, id=client_id)
        try:
            calendar = ClientCalendar.objects.get(client=client, month_name=month_name)
        except ClientCalendar.DoesNotExist:
            return Response({"error": "No calendar found for that client & month."},
                            status=status.HTTP_404_NOT_FOUND)

        new_file = request.FILES.get('monthly_reports')
        if not new_file:
            return Response({"monthly_reports": ["No file uploaded."]},
                            status=status.HTTP_400_BAD_REQUEST)

        # Remember old key so we can delete it later
        old_key = calendar.monthly_reports.name if calendar.monthly_reports else None

        tmp_path = None
        try:
            # 1) write to a temp file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                for chunk in new_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            path_in_bucket = f"reports/{new_file.name}"

            # 2) delete old if exists
            if old_key:
                try:
                    storage.remove([old_key])
                except Exception:
                    pass

            # 3) upload (or update on 409)
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
                    return Response({"monthly_reports": [msg]},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 4) save new key on the model
            calendar.monthly_reports.name = path_in_bucket
            calendar.save()

        finally:
            # cleanup
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        serializer = serializers.ClientReportSerializer(calendar, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClientMonthlyReportsRUDView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = ClientCalendar.objects.all()
    serializer_class = serializers.ClientReportSerializer

    def partial_update(self, request, *args, **kwargs):
        # we only allow updating monthly_reports via POST/PUT above
        return Response({"detail": "Use POST on the list endpoint to upload reports."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def delete(self, request, *args, **kwargs):
        calendar = self.get_object()
        if calendar.monthly_reports:
            # delete from Supabase
            key = calendar.monthly_reports.name
            try:
                storage.remove([key])
            except Exception:
                pass
            # clear the field
            calendar.monthly_reports.delete(save=True)
            calendar.save()

        return Response({"message": "Monthly report deleted successfully."},
                        status=status.HTTP_204_NO_CONTENT)
        
class ClientTeamView(generics.RetrieveAPIView):
    """Retrieve all team members related to a given client."""
    permission_classes = [IsAuthenticated]  # Requires authentication

    def get(self, request, client_id, *args, **kwargs):
        #  Ensure the client exists
        client = get_object_or_404(models.Clients, id=client_id)

        #  Get the team related to this client
        team = client.team  # Directly access the team from Clients model

        if not team:
            return Response({"error": "No team assigned to this client."}, status=status.HTTP_404_NOT_FOUND)

        #  Get all users assigned to this team via TeamMembership
        team_memberships = TeamMembership.objects.filter(team=team)
        team_users = [membership.user for membership in team_memberships]

        #  Serialize team members' data
        serialized_team = UserSerializer(team_users, many=True).data

        return Response({"client": client.business_name, "team_members": serialized_team}, status=status.HTTP_200_OK)

class ClientCustomTaskView(APIView):
    """List & Create Custom Tasks for a Client (Handled by Account Managers)."""
    permission_classes = [IsAuthenticated]
    serializer_class = CustomTaskSerializer
    parser_classes = [MultiPartParser, FormParser]  # Enable file upload

    def get(self, request, client_id, *args, **kwargs):
        client = get_object_or_404(Clients, id=client_id)

        if request.user.role != "account_manager":
            return Response({"error": "Only account managers can view tasks."}, status=status.HTTP_403_FORBIDDEN)

        if client.account_manager != request.user:
            return Response({"error": "You are not authorized to view tasks for this client."}, status=status.HTTP_403_FORBIDDEN)

        tasks = CustomTask.objects.filter(client_id=client)
        serialized_tasks = CustomTaskSerializer(tasks, many=True, context={"request": request})
        return Response({"client": client.business_name, "tasks": serialized_tasks.data}, status=status.HTTP_200_OK)

    def post(self, request, client_id, *args, **kwargs):
        client = get_object_or_404(models.Clients, id=client_id)

        if request.user.role != "account_manager":
            return Response({"error": "Only account managers can create tasks."}, status=status.HTTP_403_FORBIDDEN)

        if client.account_manager != request.user:
            return Response({"error": "You are not authorized to create tasks for this client."}, status=status.HTTP_403_FORBIDDEN)

        assign_to_id = request.data.get("assign_to_id")
        if not assign_to_id:
            return Response({"error": "assign_to_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        assigned_user = get_object_or_404(models.CustomUser, id=assign_to_id)
        if not models.TeamMembership.objects.filter(team=client.team, user=assigned_user).exists():
            return Response({"error": "User is not a member of the client's assigned team."}, status=status.HTTP_400_BAD_REQUEST)

        # Handle task file upload to Supabase
        task_file = request.FILES.get("task_file")
        path_in_bucket = None
        if task_file:
            tmp_path = None
            try:
                # Save upload to a temp file
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    for chunk in task_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                path_in_bucket = f"task_files/{task_file.name}"

                # Try upload; on 409 overwrite via update()
                try:
                    storage.upload(
                        file=tmp_path,
                        path=path_in_bucket,
                        file_options={"content-type": task_file.content_type}
                    )
                except StorageApiError as exc:
                    raw = exc.args[0] if exc.args else {}
                    if isinstance(raw, dict) and raw.get("statusCode") == 409:
                        storage.update(
                            file=tmp_path,
                            path=path_in_bucket,
                            file_options={"content-type": task_file.content_type}
                        )
                    else:
                        msg = raw.get("message", str(exc)) if isinstance(raw, dict) else str(exc)
                        return Response({"error": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                # Clean up temp file
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        # Create the task
        task = models.CustomTask.objects.create(
            task_name=request.data.get("task_name"),
            task_description=request.data.get("task_description"),
            assign_to_id=assigned_user,
            client_id=client,
            custom_task_file=path_in_bucket  # Store only the path
        )

        notification_message = f"You have been assigned a new task: {task.task_name} for client {client.business_name}."
        send_task_notification(
            recipient=assigned_user,
            sender=request.user,
            message=notification_message,
            task=task,
            notification_type="task_assigned"
        )

        return Response(serializers.CustomTaskSerializer(task, context={"request": request}).data, status=status.HTTP_201_CREATED)
