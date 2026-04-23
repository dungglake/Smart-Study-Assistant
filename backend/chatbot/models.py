from django.db import models
from django.conf import settings

class Material(models.Model):
    STATUS_CHOICES = [
        ("UPLOADED", "Uploaded"),
        ("PROCESSING", "Processing"),
        ("DONE", "Done"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="materials/")
    file_type = models.CharField(max_length=10)  
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="UPLOADED")
    progress = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} - {self.title}"

class MaterialChunk(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="chunks")
    order = models.IntegerField()
    text = models.TextField()

    embedding = models.JSONField(null=True, blank=True)  

    class Meta:
        ordering = ["order"]

class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, blank=True, default="")
    summary = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Conversation {self.id}"

class Message(models.Model):
    ROLE_CHOICES = [("user", "User"), ("assistant", "Assistant")]
    MODE_CHOICES = [("CHAT", "Chat"), ("FLASHCARD", "Flashcard"), ("QUIZ", "Quiz"), ("MINDMAP", "Mindmap")]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="CHAT")
    content = models.JSONField()  
    created_at = models.DateTimeField(auto_now_add=True)
    
class ConversationMemory(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="memories"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_memories"
    )

    source_message = models.ForeignKey(
        Message,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memory_entries"
    )

    memory_type = models.CharField(
        max_length=30,
        default="fact"
    )  # fact, preference, task, summary, profile

    text = models.TextField()
    embedding = models.JSONField(null=True, blank=True)

    importance = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-importance", "-updated_at"]