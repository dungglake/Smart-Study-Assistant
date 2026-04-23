from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from planner.models import PlanSlot, Subject, WeeklySubjectGoal
from .base import PlannerBaseAPITestCase, aware_dt, monday_of


class PlannerSubjectActionTests(PlannerBaseAPITestCase):
    def test_rename_subject_in_week_success(self):
        subject, _ = self.create_goal(name="Math", required_hours=1.0)

        url = reverse("subject-rename-in-week")
        res = self.client.post(
            url,
            {
                "week_start": self.week_start.isoformat(),
                "subject_id": subject.id,
                "new_name": "Advanced Math",
            },
            format="json",
        )

        self.assertEqual(res.status_code, 200)
        subject.refresh_from_db()
        self.assertEqual(subject.name, "Advanced Math")

    def test_rename_subject_in_week_rejects_duplicate_name(self):
        subject1, _ = self.create_goal(name="Math", required_hours=1.0)
        self.create_goal(name="Physics", required_hours=1.0)

        url = reverse("subject-rename-in-week")
        res = self.client.post(
            url,
            {
                "week_start": self.week_start.isoformat(),
                "subject_id": subject1.id,
                "new_name": "Physics",
            },
            format="json",
        )

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "A subject with this name already exists.")

    def test_delete_subject_from_week_success(self):
        subject, _ = self.create_goal(name="Math", required_hours=1.0)

        self.create_plan_slot(
            subject=subject,
            day=self.week_start + timedelta(days=1),
            start_hour=18,
            start_minute=0,
            end_hour=19,
            end_minute=0,
            kind="study",
            locked=False,
        )

        url = reverse("subject-delete-from-week")
        res = self.client.post(
            url,
            {
                "week_start": self.week_start.isoformat(),
                "subject_id": subject.id,
            },
            format="json",
        )

        self.assertEqual(res.status_code, 200)
        self.assertFalse(
            WeeklySubjectGoal.objects.filter(
                user=self.user,
                week_start=self.week_start,
                subject_id=subject.id,
            ).exists()
        )
        self.assertFalse(
            PlanSlot.objects.filter(
                user=self.user,
                subject_id=subject.id,
            ).exists()
        )

    def test_delete_subject_from_week_rejects_when_subject_is_running(self):
        current_week = monday_of(timezone.localdate())
        subject = Subject.objects.create(user=self.user, name="Math")
        WeeklySubjectGoal.objects.create(
            user=self.user,
            week_start=current_week,
            subject=subject,
            required_hours=1.0,
            priority="normal",
        )

        now = timezone.now()
        PlanSlot.objects.create(
            user=self.user,
            subject=subject,
            start=now - timedelta(minutes=30),
            end=now + timedelta(minutes=30),
            kind="study",
            locked=False,
        )

        url = reverse("subject-delete-from-week")
        res = self.client.post(
            url,
            {
                "week_start": current_week.isoformat(),
                "subject_id": subject.id,
            },
            format="json",
        )

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "This subject can no longer be modified.")

    def test_delete_subject_from_week_rejects_when_subject_already_finished(self):
        current_week = monday_of(timezone.localdate())
        subject = Subject.objects.create(user=self.user, name="Math")
        WeeklySubjectGoal.objects.create(
            user=self.user,
            week_start=current_week,
            subject=subject,
            required_hours=1.0,
            priority="normal",
        )

        now = timezone.now()
        PlanSlot.objects.create(
            user=self.user,
            subject=subject,
            start=now - timedelta(hours=2),
            end=now - timedelta(hours=1),
            kind="study",
            locked=False,
        )

        url = reverse("subject-delete-from-week")
        res = self.client.post(
            url,
            {
                "week_start": current_week.isoformat(),
                "subject_id": subject.id,
            },
            format="json",
        )

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "This subject can no longer be modified.")