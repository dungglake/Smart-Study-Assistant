from django.urls import path
from .views import (
    MaterialListCreateView,
    MaterialDetailView,
    ConversationListView,
    ConversationCreateView,
    ConversationDetailView,
    ChatView,
    ChatStreamView,
    ConversationMessagesView,
    StudioMessageDetailView,
)

urlpatterns = [
    path("materials/", MaterialListCreateView.as_view()),
    path("materials/<int:pk>/", MaterialDetailView.as_view()),
    path("conversations/", ConversationListView.as_view()),
    path("conversations/create/", ConversationCreateView.as_view()),
    path("conversations/<int:pk>/", ConversationDetailView.as_view()),
    path("conversations/<int:pk>/messages/", ConversationMessagesView.as_view()),
    path("chat/", ChatView.as_view()),
    path("chat/stream/", ChatStreamView.as_view()),
    path("studio/messages/<int:pk>/", StudioMessageDetailView.as_view()),
]