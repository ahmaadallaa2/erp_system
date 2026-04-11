from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)

from apps.partners.models import Partner
from .serializers import PartnerSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List partners",
        description=(
            "Retrieve a list of partners for the authenticated user's company. "
            "Results can be filtered by partner type and searched by name."
        ),
        tags=["Partners"],
        parameters=[
            OpenApiParameter(
                name="partner_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["customer", "supplier", "both"],
                description="Filter partners by type.",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Case-insensitive search by partner name.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve partner",
        description="Retrieve a single partner by ID for the authenticated user's company.",
        tags=["Partners"],
    ),
    create=extend_schema(
        summary="Create partner",
        description="Create a new partner under the authenticated user's company.",
        tags=["Partners"],
    ),
    update=extend_schema(
        summary="Update partner",
        description="Update an existing partner.",
        tags=["Partners"],
    ),
    partial_update=extend_schema(
        summary="Partially update partner",
        description="Partially update an existing partner.",
        tags=["Partners"],
    ),
    destroy=extend_schema(
        summary="Delete partner",
        description=(
            "Delete a partner record. "
            "Actual behavior depends on model/view logic implemented in the project."
        ),
        tags=["Partners"],
    ),
)
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

    @extend_schema(
        summary="List customers",
        description=(
            "Retrieve partners that can act as customers "
            "(partner_type = customer or both)."
        ),
        tags=["Partners"],
        responses=PartnerSerializer(many=True),
    )
    @action(detail=False, methods=["get"], url_path="customers")
    def customers(self, request):
        queryset = self.get_queryset().filter(
            partner_type__in=["customer", "both"]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="List suppliers",
        description=(
            "Retrieve partners that can act as suppliers "
            "(partner_type = supplier or both)."
        ),
        tags=["Partners"],
        responses=PartnerSerializer(many=True),
    )
    @action(detail=False, methods=["get"], url_path="suppliers")
    def suppliers(self, request):
        queryset = self.get_queryset().filter(
            partner_type__in=["supplier", "both"]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)