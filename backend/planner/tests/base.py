from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from planner.models import PlanSlot, Subject, WeekDayConfig, WeeklySubjectGoal


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def aware_dt(d: date, hour: int, minute: int = 0):
    return timezone.make_aware(datetime.combine(d, time(hour, minute)))


class PlannerBaseAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="u1",
            email="u1@example.com",
            password="pass12345",
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)
        self.week_start = monday_of(timezone.localdate() + timedelta(days=7))

    def create_subject(self, name="Math"):
        return Subject.objects.create(user=self.user, name=name)

    def create_goal(
        self,
        name="Math",
        required_hours=1.0,
        priority="normal",
        deadline=None,
        week_start=None,
    ):
        week_start = week_start or self.week_start
        subject = self.create_subject(name=name)
        goal = WeeklySubjectGoal.objects.create(
            user=self.user,
            week_start=week_start,
            subject=subject,
            required_hours=required_hours,
            priority=priority,
            deadline=deadline,
        )
        return subject, goal

    def create_day_config(self, target_date, number_of_subjects=1, week_start=None):
        week_start = week_start or self.week_start
        return WeekDayConfig.objects.create(
            user=self.user,
            week_start=week_start,
            date=target_date,
            number_of_subjects=number_of_subjects,
        )

    def create_plan_slot(
        self,
        subject,
        day,
        start_hour=18,
        start_minute=0,
        end_hour=19,
        end_minute=0,
        kind="study",
        locked=False,
    ):
        return PlanSlot.objects.create(
            user=self.user,
            subject=subject,
            start=aware_dt(day, start_hour, start_minute),
            end=aware_dt(day, end_hour, end_minute),
            kind=kind,
            locked=locked,
        )