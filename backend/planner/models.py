from django.conf import settings
from django.db import models


class Subject(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    difficulty = models.PositiveSmallIntegerField(default=3)  # 1..5

    def __str__(self):
        return f"{self.name} (d={self.difficulty})"


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
    estimate_minutes = models.PositiveIntegerField(default=50)  # tổng phút cần
    due_at = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="study")
    prereq = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.subject.name}: {self.title}"


class Availability(models.Model):
    """ Khung giờ rảnh theo tuần (0=Mon..6=Sun). Dùng khi bạn muốn lưu vào DB.
        Với endpoint generate hiện tại, ta cũng chấp nhận payload trực tiếp (không bắt buộc lưu DB).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    weekday = models.PositiveSmallIntegerField()  # 0..6
    start = models.TimeField()
    end = models.TimeField()


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
