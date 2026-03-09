from rest_framework import serializers
from .models import Material, Conversation, Message

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ["id", "title", "file", "file_type", "status", "progress", "created_at"]
        read_only_fields = ["status", "progress", "created_at"]

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "material", "created_at"]
        read_only_fields = ["created_at"]

class ChatRequestSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    mode = serializers.ChoiceField(choices=["CHAT", "FLASHCARD", "QUIZ", "MINDMAP"])
    message = serializers.CharField()