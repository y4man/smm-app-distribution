from django.conf import settings
from rest_framework import serializers
from .models import Clients, ClientsPlan
from pro_app import models
from .models import ClientInvoices
from calender.models import ClientCalendar


class ClientSerializer(serializers.ModelSerializer):
    # Get a single plan for the client, if it exists
    client_plan = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()  # Custom field for team with ID and name

    class Meta:
        model = Clients
        fields = '__all__'
        extra_kwargs = {
            'account_manager': {'required': False},
        }

    def get_client_plan(self, obj):
        # Retrieve the latest or most relevant plan for the client
        client_plan = obj.client_plans.first()  # Access the related name directly
        if not client_plan:
            return None

        # Get the client's account manager
        account_manager = obj.account_manager
        if not account_manager:
            return {"error": "Client does not have an assigned account manager."}

        # Fetch the plan associated with the account manager and the plan type
        plan_type = client_plan.plan_type
        plan = models.Plans.objects.filter(account_managers__id=account_manager.id).first()

        if not plan:
            return {"error": f"No {plan_type} plan found for the client's account manager."}

        # Add detailed plan data into the client_plan object
        client_plan_data = {
            "id": client_plan.id,
            "plan_type": client_plan.plan_type,
            "add_on_attributes": client_plan.attributes,
            "platforms": client_plan.platforms,
            # "add_ons": client_plan.add_ons,
            "grand_total": client_plan.grand_total,
            "created_at": client_plan.created_at,
            "updated_at": client_plan.updated_at,
        }

        # Include plan-specific attributes based on the plan type
        if plan_type.lower() == "standard":
            client_plan_data["plan_attributes"] = plan.standard_attributes
            client_plan_data["plan_net_price"] = plan.standard_netprice
        elif plan_type.lower() == "advanced":
            client_plan_data["plan_attributes"] = plan.advanced_attributes
            client_plan_data["plan_net_price"] = plan.advanced_netprice
        else:
            client_plan_data["error"] = f"Unknown plan type: {plan_type}"

        return client_plan_data

    def get_team(self, obj):
        # Include both team ID and name if a team is assigned
        if obj.team:
            return {
                "id": obj.team.id,
                "name": obj.team.name
            }
        return None

    # Field-level validation
    def validate_business_name(self, value):
        if Clients.objects.filter(business_name__iexact=value).exists():
            raise serializers.ValidationError("A client with this business name already exists.")
        return value

    # Object-level validation
    def validate(self, data):
        # Conditional field validation for web development data fields
        if data.get('website_type') == 'ecommerce' and not data.get('num_of_products'):
            raise serializers.ValidationError("Number of products is required for eCommerce websites.")
        if data.get('domain') == 'yes' and not data.get('domain_info'):
            raise serializers.ValidationError("Domain information is required if domain is 'yes'.")
        if data.get('hosting') == 'yes' and not data.get('hosting_info'):
            raise serializers.ValidationError("Hosting information is required if hosting is 'yes'.")
        return data
    
class ClientInvoicesSerializer(serializers.ModelSerializer):
    # Replace the default FileField with a method field
    invoice = serializers.SerializerMethodField()

    class Meta:
        model = ClientInvoices
        fields = '__all__'

    def get_invoice(self, obj):
        """
        obj.invoice is just the path in bucket, e.g. "invoices/foo.pdf".
        We turn it into the full Supabase public URL:
        <SUPABASE_URL>/storage/v1/object/public/<BUCKET>/<PATH>
        """
        return (
            f"{settings.SUPABASE_URL}"
            f"/storage/v1/object/public/"
            f"{settings.SUPABASE_BUCKET}/"
            f"{obj.invoice}"
        )


class ClientProposalSerializer(serializers.ModelSerializer):
    proposal_pdf = serializers.SerializerMethodField()

    class Meta:
        model  = Clients
        fields = ['proposal_pdf', 'proposal_approval_status']

    def get_proposal_pdf(self, obj):
        if not obj.proposal_pdf:
            return None
        # obj.proposal_pdf.name is the "proposals/..." key
        return (
            f"{settings.SUPABASE_URL}"
            f"/storage/v1/object/public/"
            f"{settings.SUPABASE_BUCKET}/"
            f"{obj.proposal_pdf.name}"
        )
class AssignClientToTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Clients
        fields = ['id', 'business_name', 'team']

class ClientsPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientsPlan
        # deleted , 'add_ons' bcz not in model..
        fields = ['plan_type', 'attributes', 'platforms', 'grand_total', 'created_at', 'updated_at']

class ClientReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientCalendar
        fields = ['id', 'client', 'month_name', 'monthly_reports']
        read_only_fields = ['id', 'client', 'month_name']
    def update(self, instance, validated_data):
        # Update only the `monthly_reports` field
        if 'monthly_reports' in validated_data:
            instance.monthly_reports = validated_data['monthly_reports']
            instance.save()
        return instance
