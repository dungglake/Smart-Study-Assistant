from django.urls import path
from .views import MaterialListCreateView, MaterialDetailView, ConversationCreateView, ChatView

urlpatterns = [
    path("materials/", MaterialListCreateView.as_view()),
    path("materials/<int:pk>/", MaterialDetailView.as_view()),
    path("conversations/", ConversationCreateView.as_view()),
    path("chat/", ChatView.as_view()),
]