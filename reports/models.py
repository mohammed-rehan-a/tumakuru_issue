from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class IssueCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='fas fa-exclamation-circle')
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#FF6B35')
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Issue Category"
        verbose_name_plural = "Issue Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class IssueReport(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    # Tracking
    report_id = models.CharField(max_length=20, unique=True, editable=False)
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    category = models.ForeignKey(IssueCategory, on_delete=models.SET_NULL, null=True)

    # Issue Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255)
    ward_number = models.CharField(max_length=5)
    landmark = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Media
    image = models.ImageField(upload_to='issue_images/%Y/%m/', blank=True, null=True)
    image2 = models.ImageField(upload_to='issue_images/%Y/%m/', blank=True, null=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    points_awarded = models.PositiveIntegerField(default=0)
    is_points_given = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Admin fields
    admin_remarks = models.TextField(blank=True)
    assigned_to = models.CharField(max_length=100, blank=True)
    upvotes = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Issue Report"
        verbose_name_plural = "Issue Reports"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.report_id}] {self.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_status = IssueReport.objects.get(pk=self.pk).status
            except IssueReport.DoesNotExist:
                pass

        if not self.report_id:
            import random, string
            prefix = "TCC"
            year = timezone.now().year
            random_part = ''.join(random.choices(string.digits, k=6))
            self.report_id = f"{prefix}{year}{random_part}"
            
        super().save(*args, **kwargs)
        
        # Trigger notifications if status changed to in_progress or resolved
        if not is_new and old_status and old_status != self.status:
            if self.status in ['in_progress', 'resolved']:
                try:
                    from reports.notifications import send_status_update_notification
                    send_status_update_notification(self, self.citizen.profile)
                except Exception as e:
                    pass  # Fail gracefully if notification fails

    def get_status_color(self):
        colors = {
            'pending': '#FFA500',
            'acknowledged': '#2196F3',
            'in_progress': '#9C27B0',
            'resolved': '#4CAF50',
            'closed': '#607D8B',
            'rejected': '#F44336',
        }
        return colors.get(self.status, '#999')

    def get_priority_color(self):
        colors = {
            'low': '#4CAF50',
            'medium': '#FFA500',
            'high': '#FF5722',
            'critical': '#F44336',
        }
        return colors.get(self.priority, '#999')

    @property
    def feedback_exists(self):
        return hasattr(self, 'feedback')

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('report_detail', kwargs={'pk': self.pk})


class IssueComment(models.Model):
    issue = models.ForeignKey(IssueReport, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    is_official = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.issue.report_id}"


class IssueUpvote(models.Model):
    issue = models.ForeignKey(IssueReport, on_delete=models.CASCADE, related_name='voters')
    citizen = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('issue', 'citizen')

class VolunteerTask(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    points_reward = models.PositiveIntegerField(default=10)
    location = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class VolunteerLog(models.Model):
    task = models.ForeignKey(VolunteerTask, on_delete=models.CASCADE, related_name='volunteers')
    citizen = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('task', 'citizen')

class ReportFeedback(models.Model):
    report = models.OneToOneField(IssueReport, on_delete=models.CASCADE, related_name='feedback')
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Report Feedback"
        verbose_name_plural = "Report Feedbacks"

    def __str__(self):
        return f"Feedback for {self.report.report_id} - {self.rating} Stars"


class EnvironmentSave(models.Model):
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='environment_saves')
    tree_image = models.ImageField(upload_to='environment_trees/%Y/%m/')
    points_awarded = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Environment Save"
        verbose_name_plural = "Environment Saves"
        ordering = ['-created_at']

    def __str__(self):
        return f"Environment Save by {self.citizen.username} (+{self.points_awarded} pts)"


class TreePlantingCertificate(models.Model):
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tree_certificates')
    environment_save = models.OneToOneField(EnvironmentSave, on_delete=models.CASCADE, related_name='certificate')
    certificate_number = models.CharField(max_length=40, unique=True)
    issued_date = models.DateTimeField(auto_now_add=True)
    tree_points = models.PositiveIntegerField(default=5)

    class Meta:
        verbose_name = "Tree Planting Certificate"
        verbose_name_plural = "Tree Planting Certificates"
        ordering = ['-issued_date']

    def __str__(self):
        return f"Tree Certificate #{self.certificate_number} — {self.citizen.username}"


class TreeMilestoneCertificate(models.Model):
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tree_milestone_certificates')
    certificate_number = models.CharField(max_length=50, unique=True)
    issued_date = models.DateTimeField(auto_now_add=True)
    milestone = models.PositiveIntegerField()  # 100, 200, 300 ...
    tree_points_at_issue = models.PositiveIntegerField()
    trees_count_at_issue = models.PositiveIntegerField(default=0)
    is_downloaded = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tree Milestone Certificate"
        verbose_name_plural = "Tree Milestone Certificates"
        ordering = ['-issued_date']

    def __str__(self):
        return f"Tree Milestone #{self.certificate_number} — {self.citizen.username}"
