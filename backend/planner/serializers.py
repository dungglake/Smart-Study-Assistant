from rest_framework import serializers


class AvailabilityItemSer(serializers.Serializer):
    weekday = serializers.IntegerField(min_value=0, max_value=6)
    start = serializers.CharField()  # "HH:MM"
    end = serializers.CharField()    # "HH:MM"


class BusyExceptionSer(serializers.Serializer):
    _from = serializers.DateTimeField(source="from")
    _to = serializers.DateTimeField(source="to")


class SubjectSer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=120)
    difficulty = serializers.IntegerField(min_value=1, max_value=5)


class TaskSer(serializers.Serializer):
    id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    estimate_minutes = serializers.IntegerField(min_value=1)
    due_at = serializers.DateTimeField(required=False, allow_null=True)
    type = serializers.ChoiceField(choices=["study", "review", "practice", "notes"], default="study")


class ExamSer(serializers.Serializer):
    id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    at = serializers.DateTimeField()
    review_pattern = serializers.ListField(child=serializers.IntegerField(), required=False)


class FocusWindowSer(serializers.Serializer):
    weekday = serializers.CharField()  # "any" hoặc 0..6
    start = serializers.CharField()
    end = serializers.CharField()


class PrefsSer(serializers.Serializer):
    week_start = serializers.DateField()
    horizon_days = serializers.IntegerField(default=7, min_value=1, max_value=14)
    session_len_min = serializers.IntegerField(default=50, min_value=20, max_value=180)
    break_min = serializers.IntegerField(default=10, min_value=0, max_value=60)
    max_daily_min = serializers.IntegerField(default=240, min_value=30, max_value=720)
    max_consecutive_sessions = serializers.IntegerField(default=3, min_value=1, max_value=8)
    easy_first_week = serializers.BooleanField(default=True)
    hard_first_day = serializers.BooleanField(default=True)
    focus_windows = FocusWindowSer(many=True, required=False)
    spaced_repetition = serializers.BooleanField(default=True)


class GeneratePlanSer(serializers.Serializer):
    availability_weekly = AvailabilityItemSer(many=True)
    busy_exceptions = BusyExceptionSer(many=True, required=False)
    subjects = SubjectSer(many=True)
    tasks = TaskSer(many=True, required=False)
    exams = ExamSer(many=True, required=False)
    prefs = PrefsSer()
