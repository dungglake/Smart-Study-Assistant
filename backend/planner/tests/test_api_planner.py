from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from planner.models import BusyBlock, WeeklySubjectGoal, Subject, PlanSlot


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


class PlannerAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="u1", email="u1@example.com", password="pass12345")

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_health_check(self):
        url = reverse("planner-health")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data.get("status"), "ok")

    def test_get_busy_week_requires_week_start(self):
        url = reverse("busy-week-get")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 400)

    def test_autosave_requires_busy_or_subjects(self):
        url = reverse("week-autosave")
        week_start = monday_of(date(2025, 11, 24))
        res = self.client.post(url, {"week_start": week_start}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_autosave_busy_without_sleep_saves_and_warns(self):
        url = reverse("week-autosave")
        week_start = monday_of(date(2025, 11, 24))

        payload = {
            "week_start": week_start,
            "busy": [
                {"date": "2025-11-24", "start": "07:00", "end": "17:00", "type": "school"},
            ]
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, 200)

        self.assertTrue(res.data["saved"]["busy"])
        self.assertTrue(res.data["sleep_missing"])  # thiếu sleep => True
        self.assertTrue(isinstance(res.data.get("warnings", []), list))

        # DB saved
        ws = week_start
        we = week_start + timedelta(days=7)
        self.assertEqual(BusyBlock.objects.filter(user=self.user, date__gte=ws, date__lt=we).count(), 1)

    def test_get_busy_week_auto_copy_from_prev_week(self):
        prev_week = monday_of(date(2025, 11, 17))
        next_week = monday_of(date(2025, 11, 24))

        # prev week busy includes sleep
        BusyBlock.objects.create(user=self.user, date=prev_week, start="07:00", end="17:00", type="school")
        BusyBlock.objects.create(user=self.user, date=prev_week, start="23:00", end="06:00", type="sleep")

        url = reverse("busy-week-get")
        res = self.client.get(url, {"week_start": next_week.isoformat()})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["auto_copied"])
        self.assertEqual(res.data["source_week_start"], prev_week.isoformat())

        # DB now has copied records for next week
        ws = next_week
        we = next_week + timedelta(days=7)
        self.assertGreaterEqual(BusyBlock.objects.filter(user=self.user, date__gte=ws, date__lt=we).count(), 2)

    def test_goals_week_post_and_get(self):
        week_start = monday_of(date(2025, 11, 24))
        url = reverse("goals-week")

        payload = {
            "week_start": week_start,
            "subjects": [
                {"name": "Math", "required_hours": 2.0, "deadline": None},
                {"name": "English", "required_hours": 3.0, "deadline": None},
            ]
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["saved"], 2)

        # GET
        res2 = self.client.get(url, {"week_start": week_start.isoformat()})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.data["count"], 2)

        self.assertEqual(
            WeeklySubjectGoal.objects.filter(user=self.user, week_start=week_start).count(),
            2
        )

    def test_generate_plan_week_no_subjects_returns_400(self):
        week_start = monday_of(date(2025, 11, 24))
        url = reverse("plan-generate-week")
        res = self.client.post(url, {"week_start": week_start}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data.get("code"), "NO_SUBJECTS")

    def test_generate_plan_week_requires_sleep_option_a(self):
        week_start = monday_of(date(2025, 11, 24))
        url = reverse("plan-generate-week")

        payload = {
            "week_start": week_start,
            "busy": [
                {"date": "2025-11-24", "start": "07:00", "end": "17:00", "type": "school"},
                # thiếu sleep
            ],
            "subjects": [
                {"name": "Math", "required_hours": 1.0, "deadline": None},
            ]
        }
        res = self.client.post(url, payload, format="json")

        # Option A expected:
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data.get("code"), "NO_SLEEP")

    def test_generate_plan_week_success_persists_plan(self):
        week_start = monday_of(date(2025, 11, 24))
        url = reverse("plan-generate-week")

        payload = {
            "week_start": week_start,
            "busy": [
                {"date": "2025-11-24", "start": "07:00", "end": "17:00", "type": "school"},
                {"date": "2025-11-24", "start": "23:00", "end": "06:00", "type": "sleep"},
            ],
            "subjects": [
                {"name": "Math", "required_hours": 1.0, "deadline": None},
                {"name": "English", "required_hours": 2.0, "deadline": None},
            ]
        }
        res = self.client.post(url, payload, format="json")

        # Nếu bạn đang chặn NO_SLEEP, case này có sleep => 200
        self.assertEqual(res.status_code, 200)
        self.assertIn("plan", res.data)
        self.assertTrue(isinstance(res.data["plan"], list))

        # Plan saved to DB
        ws = week_start
        we = week_start + timedelta(days=7)
        self.assertGreaterEqual(
            PlanSlot.objects.filter(user=self.user, start__date__gte=ws, start__date__lt=we).count(),
            1
        )

    def test_get_plan_week_returns_saved_plan(self):
        week_start = monday_of(date(2025, 11, 24))
        ws = week_start
        dt = timezone.make_aware(timezone.datetime(2025, 11, 24, 18, 0, 0))
        dt2 = timezone.make_aware(timezone.datetime(2025, 11, 24, 19, 0, 0))

        subj = Subject.objects.create(user=self.user, name="Math")
        PlanSlot.objects.create(user=self.user, subject=subj, start=dt, end=dt2, kind="study", locked=False)

        url = reverse("plan-week-get")
        res = self.client.get(url, {"week_start": ws.isoformat()})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)

    def test_delete_plan_week_deletes_unlocked(self):
        week_start = monday_of(date(2025, 11, 24))
        dt = timezone.make_aware(timezone.datetime(2025, 11, 24, 18, 0, 0))
        dt2 = timezone.make_aware(timezone.datetime(2025, 11, 24, 19, 0, 0))
        subj = Subject.objects.create(user=self.user, name="Math")

        PlanSlot.objects.create(user=self.user, subject=subj, start=dt, end=dt2, kind="study", locked=False)

        url = reverse("plan-week-delete") + f"?week_start={week_start.isoformat()}"
        res = self.client.delete(url)
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.data["deleted"], 1)

    def test_week_status_counts(self):
        week_start = monday_of(date(2025, 11, 24))
        ws = week_start
        we = week_start + timedelta(days=7)

        BusyBlock.objects.create(user=self.user, date=ws, start="23:00", end="06:00", type="sleep")
        Subject.objects.create(user=self.user, name="Math")
        subj = Subject.objects.get(user=self.user, name="Math")
        WeeklySubjectGoal.objects.create(user=self.user, week_start=ws, subject=subj, required_hours=1.0)

        url = reverse("week-status")
        res = self.client.get(url, {"week_start": ws.isoformat()})
        self.assertEqual(res.status_code, 200)
        self.assertIn("server_counts", res.data)
        self.assertIn("sleep", res.data["server_counts"])
