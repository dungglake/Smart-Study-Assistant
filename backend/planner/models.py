from django.conf import settings
from django.db import models

class Subject(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_subject_per_user"
            )
        ]

    def __str__(self):
        return self.name

class StudyTask(models.Model):
    TYPE_CHOICES = (
        ("study", "Study"),
        ("review", "Review"),
        ("practice", "Practice"),
        ("notes", "Notes"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    estimate_minutes = models.PositiveIntegerField(default=50)  
    due_at = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="study")
    prereq = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.subject.name}: {self.title}"

class PlanSlot(models.Model):
    """ Lịch đã xếp """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, null=True, blank=True, on_delete=models.SET_NULL)
    task = models.ForeignKey(StudyTask, null=True, blank=True, on_delete=models.SET_NULL)
    start = models.DateTimeField()
    end = models.DateTimeField()
    kind = models.CharField(max_length=20, default="study")  # study/review/break
    locked = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["user", "start"])]
        ordering = ["start"]
class BusyBlock(models.Model):
    TYPE_CHOICES = (
        ("school", "School"),
        ("work", "Work"),
        ("sleep", "Sleep"),
        ("other", "Other"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    start = models.TimeField()
    end = models.TimeField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="other")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "date"]),
        ]
        ordering = ["date", "start"]

    def __str__(self):
        return f"{self.user_id} {self.date} {self.start}-{self.end} ({self.type})"

class WeeklySubjectGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    week_start = models.DateField()  
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE)
    required_hours = models.FloatField(default=1.0)
    deadline = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "week_start"])]
        ordering = ["week_start", "subject_id"]

    def __str__(self):
        return f"{self.user_id} {self.week_start} {self.subject_id} {self.required_hours}h"