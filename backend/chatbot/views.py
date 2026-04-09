import os
import threading
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Material, MaterialChunk, Conversation, Message
from .serializers import (
    MaterialSerializer,
    ConversationSerializer,
    ChatRequestSerializer,
    MessageSerializer,
)
from .utils import extract_text_from_file, chunk_text
from .engine import retrieve_top_chunks, generate_response, suggest_title_and_summary


def process_material(material_id, user):
    material = Material.objects.get(id=material_id, user=user)

    try:
        path = material.file.path
        ext = material.file_type

        text = extract_text_from_file(path, ext)
        material.progress = 40
        material.save(update_fields=["progress"])

        chunks = chunk_text(text, max_chars=1200)
        objs = [
            MaterialChunk(material=material, order=i, text=ch)
            for i, ch in enumerate(chunks, start=1)
        ]
        MaterialChunk.objects.bulk_create(objs)

        material.progress = 85
        material.save(update_fields=["progress"])

        _, conv_summary = suggest_title_and_summary(material)

        first_response = conv_summary.strip() or f"Đã tải xong tài liệu: {material.title}"
        title_from_response = first_response[:255]

        conv = Conversation.objects.create(
            user=user,
            material=material,
            title=title_from_response,
            summary=first_response,
        )

        Message.objects.create(
            conversation=conv,
            role="assistant",
            mode="CHAT",
            content={"text": first_response},
        )

        material.status = "DONE"
        material.progress = 100
        material.save(update_fields=["status", "progress"])

    except Exception:
        material.status = "FAILED"
        material.save(update_fields=["status"])


class MaterialListCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")
        title = request.data.get("title") or (file.name if file else "Untitled")

        if not file:
            return Response({"detail": "file is required"}, status=400)

        ext = os.path.splitext(file.name)[1].lower().replace(".", "")
        if ext not in ["pdf", "txt", "docx", "md"]:
            return Response({"detail": "Only pdf, txt, docx, md supported"}, status=400)

        material = Material.objects.create(
            user=request.user,
            title=title,
            file=file,
            file_type=ext,
            status="PROCESSING",
            progress=5,
        )

        threading.Thread(
            target=process_material,
            args=(material.id, request.user),
            daemon=True,
        ).start()

        return Response(
            {
                "material_id": material.id,
                "status": material.status,
                "progress": material.progress,
            },
            status=202,
        )


class MaterialDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        material = Material.objects.get(pk=pk, user=request.user)
        return Response(MaterialSerializer(material).data)


class ConversationListView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        material_id = request.query_params.get("material_id")
        qs = (
            Conversation.objects.filter(user=request.user)
            .select_related("material")
            .order_by("-created_at")
        )

        if material_id:
            qs = qs.filter(material_id=material_id)

        return Response(ConversationSerializer(qs, many=True).data)


class ConversationCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        material_id = serializer.validated_data["material"].id
        material = Material.objects.get(id=material_id, user=request.user)

        conv = Conversation.objects.create(
            user=request.user,
            material=material,
            title=serializer.validated_data.get("title", "") or material.title,
            summary=serializer.validated_data.get("summary", ""),
        )

        return Response(ConversationSerializer(conv).data, status=201)


class ConversationDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        conv = Conversation.objects.get(id=pk, user=request.user)

        title = request.data.get("title")
        summary = request.data.get("summary")

        update_fields = []

        if title is not None:
            conv.title = title.strip()
            update_fields.append("title")

        if summary is not None:
            conv.summary = summary.strip()
            update_fields.append("summary")

        if update_fields:
            conv.save(update_fields=update_fields)

        return Response(ConversationSerializer(conv).data)

    def delete(self, request, pk):
        conv = Conversation.objects.get(id=pk, user=request.user)
        conv.delete()
        return Response(status=204)


class ChatView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = ChatRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        conversation_id = s.validated_data["conversation_id"]
        mode = s.validated_data["mode"]
        user_message = s.validated_data["message"]

        conv = Conversation.objects.get(id=conversation_id, user=request.user)

        user_msg = Message.objects.create(
            conversation=conv,
            role="user",
            mode=mode,
            content={"text": user_message},
        )

        retrieved_chunks = retrieve_top_chunks(conv.material_id, user_message, k=4)
        content = generate_response(mode, user_message, retrieved_chunks)

        assistant_msg = Message.objects.create(
            conversation=conv,
            role="assistant",
            mode=mode,
            content=content,
        )

        return Response(
            {
                "user_message": MessageSerializer(user_msg).data,
                "assistant_message": MessageSerializer(assistant_msg).data,
            },
            status=200,
        )


class ConversationMessagesView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        conv = Conversation.objects.get(id=pk, user=request.user)
        messages = conv.messages.order_by("created_at")
        return Response(MessageSerializer(messages, many=True).data)