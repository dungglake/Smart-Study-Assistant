from datetime import time, timedelta

from django.urls import reverse
from django.utils import timezone

from planner.models import BusyBlock, PlanSlot, Subject, WeekDayConfig, WeeklySubjectGoal
from .base import PlannerBaseAPITestCase


class PlannerBusyAndStatusTests(PlannerBaseAPITestCase):
    def test_health_check(self):
        url = reverse("health-check")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {"status": "ok"})

    def test_get_busy_week_requires_week_start(self):
        url = reverse("busy-week-get")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "week_start is required")

    def test_autosave_requires_at_least_one_field(self):
        url = reverse("week-autosave")
        res = self.client.post(
            url,
            {"week_start": self.week_start.isoformat()},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_get_busy_week_auto_copy_from_previous_week(self):
        prev_week = self.week_start - timedelta(days=7)

        BusyBlock.objects.create(
            user=self.user,
            date=prev_week,
            start=time(8, 0),
            end=time(10, 0),
            type="school",
        )
        BusyBlock.objects.create(
            user=self.user,
            date=prev_week + timedelta(days=1),
            start=time(13, 0),
            end=time(15, 0),
            type="work",
        )

        url = reverse("busy-week-get")
        res = self.client.get(url, {"week_start": self.week_start.isoformat()})

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["auto_copied"])
        self.assertEqual(res.data["source_week_start"], prev_week.isoformat())
        self.assertEqual(res.data["count"], 2)

        copied = BusyBlock.objects.filter(
            user=self.user,
            date__gte=self.week_start,
            date__lt=self.week_start + timedelta(days=7),
        )
        self.assertEqual(copied.count(), 2)

    def test_autosave_week_saves_busy_subjects_day_configs(self):
        url = reverse("week-autosave")
        payload = {
            "week_start": self.week_start.isoformat(),
            "busy": [
                {
                    "date": self.week_start.isoformat(),
                    "start": "08:00",
                    "end": "10:00",
                    "type": "school",
                }
            ],
            "subjects": [
                {
                    "name": "Math",
                    "required_hours": 1.5,
                    "priority": "high",
                }
            ],
            "day_configs": [
                {
                    "date": (self.week_start + timedelta(days=1)).isoformat(),
                    "number_of_subjects": 1,
                }
            ],
        }

        res = self.client.post(url, payload, format="json")

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["saved"]["busy"])
        self.assertTrue(res.data["saved"]["subjects"])
        self.assertTrue(res.data["saved"]["day_configs"])
        self.assertFalse(res.data["sleep_missing"])

        self.assertIn("applied", res.data)

        self.assertEqual(BusyBlock.objects.filter(user=self.user).count(), 1)
        self.assertEqual(WeeklySubjectGoal.objects.filter(user=self.user).count(), 1)
        self.assertEqual(WeekDayConfig.objects.filter(user=self.user).count(), 1)

    def test_week_status_counts_busy_subjects_and_plan(self):
        subject = Subject.objects.create(user=self.user, name="Math")
        WeeklySubjectGoal.objects.create(
            user=self.user,
            week_start=self.week_start,
            subject=subject,
            required_hours=1.0,
            priority="normal",
        )

        BusyBlock.objects.create(
            user=self.user,
            date=self.week_start,
            start=time(8, 0),
            end=time(10, 0),
            type="school",
        )
        self.create_plan_slot(
            subject=subject,
            day=self.week_start,
            start_hour=18,
            start_minute=0,
            end_hour=19,
            end_minute=0,
            kind="study",
            locked=False,
        )

        url = reverse("week-status")
        res = self.client.get(url, {"week_start": self.week_start.isoformat()})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["server_counts"]["busy"], 1)
        self.assertEqual(res.data["server_counts"]["subjects"], 1)
        self.assertEqual(res.data["server_counts"]["plan"], 1)
        self.assertEqual(res.data["server_counts"]["sleep"], 0)
        self.assertTrue(res.data["has_goals"])
        self.assertTrue(res.data["has_plan"])

    def test_week_summary_returns_daily_breakdown(self):
        subject = Subject.objects.create(user=self.user, name="Math")
        WeeklySubjectGoal.objects.create(
            user=self.user,
            week_start=self.week_start,
            subject=subject,
            required_hours=1.0,
            priority="normal",
        )
        WeekDayConfig.objects.create(
            user=self.user,
            week_start=self.week_start,
            date=self.week_start,
            number_of_subjects=1,
        )

        BusyBlock.objects.create(
            user=self.user,
            date=self.week_start,
            start=time(0, 0),
            end=time(23, 59),
            type="other",
        )
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

        url = reverse("week-summary")
        res = self.client.get(url, {"week_start": self.week_start.isoformat()})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["week_start"], self.week_start.isoformat())
        self.assertEqual(len(res.data["daily"]), 7)