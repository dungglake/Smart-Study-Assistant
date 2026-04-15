from rest_framework import serializers
class BusyItemSer(serializers.Serializer):
    date = serializers.DateField()
    start = serializers.TimeField()
    end = serializers.TimeField()
    type = serializers.CharField(required=False, allow_blank=True, default="other")
class SubjectGoalSer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=120)
    studyTime = serializers.CharField(required=False)
    required_hours = serializers.FloatField(required=False, min_value=0.1)
    priority = serializers.ChoiceField(
        choices=["urgent", "high", "normal", "low"],
        default="normal"
    )
    deadline = serializers.DateTimeField(required=False, allow_null=True)
class DayConfigSer(serializers.Serializer):
    date = serializers.DateField()
    number_of_subjects = serializers.IntegerField(min_value=0, default=0)
class SaveGoalsWeekSer(serializers.Serializer):
    week_start = serializers.DateField()
    subjects = SubjectGoalSer(many=True)
class GenerateWeekSer(serializers.Serializer):
    week_start = serializers.DateField()
    busy = BusyItemSer(many=True, required=False)
    subjects = SubjectGoalSer(many=True, required=False)
class WeekAutoSaveSer(serializers.Serializer):
    week_start = serializers.DateField()
    busy = BusyItemSer(many=True, required=False)
    subjects = SubjectGoalSer(many=True, required=False)
    day_configs = DayConfigSer(many=True, required=False)

    def validate(self, attrs):
        if "busy" not in attrs and "subjects" not in attrs and "day_configs" not in attrs:
            raise serializers.ValidationError(
                "Provide at least 'busy', 'subjects', or 'day_configs'."
            )
        return attrs