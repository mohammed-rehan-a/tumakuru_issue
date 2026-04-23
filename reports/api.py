from rest_framework import viewsets, permissions
from .models import IssueCategory, IssueReport
from accounts.models import CitizenProfile
from .serializers import IssueCategorySerializer, IssueReportSerializer
from accounts.serializers import CitizenProfileSerializer

class IssueCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IssueCategory.objects.filter(is_active=True)
    serializer_class = IssueCategorySerializer
    permission_classes = [permissions.AllowAny]

class IssueReportViewSet(viewsets.ModelViewSet):
    queryset = IssueReport.objects.all()
    serializer_class = IssueReportSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(citizen=self.request.user)

class CitizenProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CitizenProfile.objects.all()
    serializer_class = CitizenProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own profile
        return CitizenProfile.objects.filter(user=self.request.user)
