import uuid
from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Participant(models.Model):
    student_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    attended = models.BooleanField(default=False)
    score = models.IntegerField(null=True, blank=True)
    certificate_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    feedback_submitted = models.BooleanField(default=False)
    feedback_rating = models.IntegerField(null=True, blank=True)
    feedback_comments = models.TextField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_screenshot = models.ImageField(upload_to='transactions/', blank=True, null=True)
    payment_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.event.name})"

    @property
    def level(self):
        if self.score is None:
            return None
        if self.score >= 90:
            return 'Gold'
        elif self.score >= 75:
            return 'Silver'
        elif self.score >= 60:
            return 'Bronze'
        else:
            return None

    @property
    def level_color(self):
        colors = {'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
        return colors.get(self.level, '#888')

    class Meta:
        ordering = ['-registered_at']
