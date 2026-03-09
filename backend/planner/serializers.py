from rest_framework import serializers
class BusyItemSer(serializers.Serializer):
    date = serializers.DateField()
    start = serializers.TimeField()
    end = serializers.TimeField()
    type = serializers.CharField(required=False, allow_blank=True, default="other")

class SubjectGoalSer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    required_hours = serializers.FloatField(min_value=0.1)
    deadline = serializers.DateTimeField(required=False, allow_null=True)
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

    def validate(self, attrs):
        if "busy" not in attrs and "subjects" not in attrs:
            raise serializers.ValidationError("Provide at least 'busy' or 'subjects' to autosave.")
        return attrs