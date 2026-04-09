from rest_framework import serializers
from .models import Material, Conversation, Message

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ["id", "title", "file", "file_type", "status", "progress", "created_at"]
        read_only_fields = ["status", "progress", "created_at"]

class ConversationSerializer(serializers.ModelSerializer):
    material_title = serializers.CharField(source="material.title", read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "material", "material_title", "title", "summary", "created_at"]
        read_only_fields = ["created_at"]

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "conversation", "role", "mode", "content", "created_at"]

class ChatRequestSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    mode = serializers.ChoiceField(choices=["CHAT", "FLASHCARD", "QUIZ", "MINDMAP"])
    message = serializers.CharField()