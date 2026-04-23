from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class CitizenProfile(models.Model):
    WARD_CHOICES = [
        (str(i), f"Ward {i}") for i in range(1, 36)
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    ward_number = models.CharField(max_length=5, choices=WARD_CHOICES, blank=True)
    aadhaar_last4 = models.CharField(max_length=4, blank=True, verbose_name="Aadhaar Last 4 Digits")
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    points = models.PositiveIntegerField(default=0)
    total_reports = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    joined_date = models.DateField(auto_now_add=True)
    bio = models.TextField(blank=True, max_length=300)

    class Meta:
        verbose_name = "Citizen Profile"
        verbose_name_plural = "Citizen Profiles"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.points} pts"

    def get_level(self):
        if self.points >= 200:
            return "Platinum Citizen"
        elif self.points >= 100:
            return "Gold Citizen"
        elif self.points >= 50:
            return "Silver Citizen"
        elif self.points >= 20:
            return "Bronze Citizen"
        else:
            return "New Citizen"

    def get_level_badge_color(self):
        level = self.get_level()
        colors = {
            "Platinum Citizen": "#E5E4E2",
            "Gold Citizen": "#FFD700",
            "Silver Citizen": "#C0C0C0",
            "Bronze Citizen": "#CD7F32",
            "New Citizen": "#4CAF50",
        }
        return colors.get(level, "#4CAF50")

    def points_to_next_certificate(self):
        """Points needed to reach the next 100-point milestone."""
        from django.conf import settings
        threshold = settings.POINTS_FOR_CERTIFICATE
        remaining = threshold - (self.points % threshold)
        if remaining == threshold:
            return 0
        return remaining

    def certificates_earned(self):
        from django.conf import settings
        return self.points // settings.POINTS_FOR_CERTIFICATE

    @property
    def progress_percentage(self):
        from django.conf import settings
        threshold = settings.POINTS_FOR_CERTIFICATE
        return min((self.points % threshold) / threshold * 100, 100)


class CitizenCertificate(models.Model):
    citizen = models.ForeignKey(CitizenProfile, on_delete=models.CASCADE, related_name='certificates')
    certificate_number = models.CharField(max_length=30, unique=True)
    issued_date = models.DateTimeField(auto_now_add=True)
    points_at_issue = models.PositiveIntegerField()
    milestone = models.PositiveIntegerField()  # e.g. 100, 200, 300
    is_downloaded = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Best Citizen Certificate"
        verbose_name_plural = "Best Citizen Certificates"
        ordering = ['-issued_date']

    def __str__(self):
        return f"Certificate #{self.certificate_number} — {self.citizen.user.get_full_name()}"


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        CitizenProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class OTPToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_tokens')
    token = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        from django.utils import timezone
        import datetime
        if self.is_used:
            return False
        # OTP valid for 10 minutes
        if timezone.now() > self.created_at + datetime.timedelta(minutes=10):
            return False
        return True

    def __str__(self):
        return f"OTP for {self.user.username}"
