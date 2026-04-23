from datetime import timedelta

from django.urls import reverse

from planner.models import PlanSlot, Subject
from .base import PlannerBaseAPITestCase, aware_dt


class PlannerPlanApiTests(PlannerBaseAPITestCase):
    def test_goals_week_post_and_get(self):
        url = reverse("goals-week")

        payload = {
            "week_start": self.week_start.isoformat(),
            "subjects": [
                {"name": "Math", "required_hours": 2.0, "priority": "high"},
                {"name": "English", "studyTime": "03:30", "priority": "normal"},
            ],
        }

        post_res = self.client.post(url, payload, format="json")
        self.assertEqual(post_res.status_code, 200)
        self.assertEqual(post_res.data["saved"], 2)

        get_res = self.client.get(url, {"week_start": self.week_start.isoformat()})
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.data["count"], 2)

        names = {item["name"] for item in get_res.data["subjects"]}
        self.assertEqual(names, {"Math", "English"})

    def test_preview_plan_week_returns_400_when_no_subjects(self):
        url = reverse("plan-preview-week")
        res = self.client.post(
            url,
            {"week_start": self.week_start.isoformat()},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["code"], "NO_SUBJECTS")

    def test_apply_plan_week_returns_400_when_no_subjects(self):
        url = reverse("plan-apply-week")
        res = self.client.post(
            url,
            {"week_start": self.week_start.isoformat()},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["code"], "NO_SUBJECTS")

    def test_apply_plan_week_persists_plan(self):
        target_day = self.week_start + timedelta(days=1)
        self.create_goal(name="Math", required_hours=1.0)
        self.create_day_config(target_day, number_of_subjects=1)

        url = reverse("plan-apply-week")
        res = self.client.post(
            url,
            {"week_start": self.week_start.isoformat()},
            format="json",
        )

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["applied"])
        self.assertIn("plan", res.data)
        self.assertGreaterEqual(len(res.data["plan"]), 1)

        saved_slots = PlanSlot.objects.filter(
            user=self.user,
            start__gte=aware_dt(self.week_start, 0, 0),
            start__lt=aware_dt(self.week_start + timedelta(days=7), 0, 0),
        )
        self.assertGreaterEqual(saved_slots.count(), 1)

    def test_get_plan_week_returns_saved_plan(self):
        subject = Subject.objects.create(user=self.user, name="Math")
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

        url = reverse("plan-week-get")
        res = self.client.get(url, {"week_start": self.week_start.isoformat()})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["plan"][0]["subject_name"], "Math")

    def test_delete_plan_week_deletes_unlocked_only(self):
        subject = Subject.objects.create(user=self.user, name="Math")

        self.create_plan_slot(
            subject=subject,
            day=self.week_start,
            start_hour=18,
            end_hour=19,
            locked=False,
        )
        self.create_plan_slot(
            subject=subject,
            day=self.week_start + timedelta(days=1),
            start_hour=18,
            end_hour=19,
            locked=True,
        )

        url = reverse("plan-week-delete")
        res = self.client.delete(f"{url}?week_start={self.week_start.isoformat()}")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(PlanSlot.objects.filter(user=self.user).count(), 1)
        self.assertTrue(PlanSlot.objects.filter(user=self.user, locked=True).exists())

    def test_delete_plan_week_force_deletes_locked_too(self):
        subject = Subject.objects.create(user=self.user, name="Math")

        self.create_plan_slot(
            subject=subject,
            day=self.week_start,
            start_hour=18,
            end_hour=19,
            locked=True,
        )

        url = reverse("plan-week-delete")
        res = self.client.delete(
            f"{url}?week_start={self.week_start.isoformat()}&force=1"
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(PlanSlot.objects.filter(user=self.user).count(), 0)

    def test_autosave_week_with_busy_and_existing_goals_auto_applies_plan(self):
        target_day = self.week_start + timedelta(days=1)
        self.create_goal(name="Math", required_hours=1.0)
        self.create_day_config(target_day, number_of_subjects=1)

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
        }

        res = self.client.post(url, payload, format="json")

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["saved"]["busy"])
        self.assertTrue(res.data["applied"])
        self.assertIn("plan", res.data)
        self.assertIn("summary", res.data)
        self.assertTrue(isinstance(res.data["warnings"], list))
        self.assertGreaterEqual(PlanSlot.objects.filter(user=self.user).count(), 1)