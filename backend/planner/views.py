from django.shortcuts import render

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from .models import Subject
# backend/planner/views.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok", "app": "planner"})

class SubjectViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subject.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

