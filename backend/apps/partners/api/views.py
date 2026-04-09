from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action

from apps.partners.models import Partner
from .serializers import PartnerSerializer
from rest_framework.response import Response


class PartnerViewSet(viewsets.ModelViewSet):
    serializer_class = PartnerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = Partner.objects.filter(
            is_deleted=False,
            company=user.company,
        ).order_by("name")

        partner_type = self.request.query_params.get("partner_type")
        if partner_type in ["customer", "supplier", "both"]:
            qs = qs.filter(partner_type=partner_type)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        return qs

    def perform_create(self, serializer):
        user = self.request.user

        if not user.company:
            raise ValidationError("Authenticated user is not assigned to a company.")

        serializer.save(company=user.company)

    @action(detail=False, methods=["get"], url_path="customers")
    def customers(self, request):
        queryset = self.get_queryset().filter(
            partner_type__in=["customer", "both"]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="suppliers")
    def suppliers(self, request):
        queryset = self.get_queryset().filter(
            partner_type__in=["supplier", "both"]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)