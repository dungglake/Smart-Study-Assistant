import os
import json
import time
import threading

from django.http import StreamingHttpResponse
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
from .engine import (
    retrieve_for_level2_chat,
    generate_response,
    suggest_title_and_summary,
    choose_dynamic_k,
)

try:
    from .embedding import get_embedding
except Exception:
    get_embedding = None


def get_recent_history(conversation, limit: int = 6):
    messages = conversation.messages.order_by("-created_at")[:limit]
    history = []
    for msg in reversed(list(messages)):
        text = ""
        if isinstance(msg.content, dict):
            text = msg.content.get("text", "")
        else:
            text = str(msg.content)
        history.append({"role": msg.role, "text": text})
    return history

def build_studio_default_title(conv, mode: str) -> str:
    if mode == "FLASHCARD":
        count = Message.objects.filter(
            conversation=conv,
            role="assistant",
            mode="FLASHCARD",
        ).count()
        return f"Flash card {count + 1}"

    if mode == "QUIZ":
        count = Message.objects.filter(
            conversation=conv,
            role="assistant",
            mode="QUIZ",
        ).count()
        return f"Quiz {count + 1}"

    return ""

def process_material(material_id, user):
    material = Material.objects.get(id=material_id, user=user)

    try:
        path = material.file.path
        ext = material.file_type

        text = extract_text_from_file(path, ext)
        material.progress = 40
        material.save(update_fields=["progress"])

        try:
            chunks = chunk_text(text, max_chars=1200, overlap_chars=180)
        except TypeError:
            chunks = chunk_text(text, max_chars=1200)

        objs = []
        for i, ch in enumerate(chunks, start=1):
            emb = None
            if get_embedding is not None:
                try:
                    emb = get_embedding(ch[:800])
                except Exception:
                    emb = None

            objs.append(
                MaterialChunk(
                    material=material,
                    order=i,
                    text=ch,
                    embedding=emb,
                )
            )

        MaterialChunk.objects.bulk_create(objs)

        material.progress = 85
        material.save(update_fields=["progress"])

        conv_title, _ = suggest_title_and_summary(material)
        Conversation.objects.create(
            user=user,
            material=material,
            title=(conv_title or material.title)[:255],
            summary="",
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

    def get_object(self, request, pk):
        return Material.objects.get(pk=pk, user=request.user)

    def get(self, request, pk):
        material = self.get_object(request, pk)
        return Response(MaterialSerializer(material).data)

    def patch(self, request, pk):
        material = self.get_object(request, pk)

        title = (request.data.get("title") or "").strip()
        if not title:
            return Response({"detail": "title is required"}, status=400)

        material.title = title
        material.save(update_fields=["title"])

        material.conversations.all().update(title=title)

        return Response(MaterialSerializer(material).data)

    def delete(self, request, pk):
        material = self.get_object(request, pk)
        material.delete()
        return Response(status=204)


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
            clean_title = title.strip()
            conv.title = clean_title
            conv.material.title = clean_title
            conv.material.save(update_fields=["title"])
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

        history = get_recent_history(conv, limit=6)
        dynamic_k = choose_dynamic_k(user_message, conversation_history=history)
        retrieved_chunks = retrieve_for_level2_chat(
            conv.material_id,
            user_message,
            k=dynamic_k,
            conversation_history=history,
        )
        content = generate_response(
            mode,
            user_message,
            retrieved_chunks,
            material_id=conv.material_id,
            conversation_history=history,
        )

        default_title = build_studio_default_title(conv, mode)

        assistant_msg = Message.objects.create(
            conversation=conv,
            role="assistant",
            mode=mode,
            title=default_title,
            content=content,
        )

        return Response(
            {
                "user_message": MessageSerializer(user_msg).data,
                "assistant_message": MessageSerializer(assistant_msg).data,
            },
            status=200,
        )


class ChatStreamView(APIView):
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

        history = get_recent_history(conv, limit=6)
        dynamic_k = choose_dynamic_k(user_message, conversation_history=history)
        retrieved_chunks = retrieve_for_level2_chat(
            conv.material_id,
            user_message,
            k=dynamic_k,
            conversation_history=history,
        )

        content = generate_response(
            mode,
            user_message,
            retrieved_chunks,
            material_id=conv.material_id,
            conversation_history=history,
        )

        if mode in ["QUIZ", "FLASHCARD"]:
            default_title = build_studio_default_title(conv, mode)

            assistant_msg = Message.objects.create(
                conversation=conv,
                role="assistant",
                mode=mode,
                title=default_title,
                content=content,
            )

            return Response(
                {
                    "user_message": MessageSerializer(user_msg).data,
                    "assistant_message": MessageSerializer(assistant_msg).data,
                },
                status=200,
            )

        full_text = ""
        if isinstance(content, dict):
            full_text = content.get("text", "")
            if not isinstance(full_text, str):
                full_text = json.dumps(content, ensure_ascii=False)
        else:
            full_text = str(content)

        citations = content.get("citations", []) if isinstance(content, dict) else []

        def chunk_text_for_stream(text: str, size: int = 24):
            for i in range(0, len(text), size):
                yield text[i:i + size]

        def stream_generator():
            try:
                yield f"data: {json.dumps({'type': 'start', 'user_message': MessageSerializer(user_msg).data}, ensure_ascii=False)}\n\n"

                built = ""
                for token in chunk_text_for_stream(full_text, size=24):
                    built += token
                    yield f"data: {json.dumps({'type': 'token', 'token': token}, ensure_ascii=False)}\n\n"
                    time.sleep(0.01)

                final_content = {"text": built, "citations": citations}

                assistant_msg = Message.objects.create(
                    conversation=conv,
                    role="assistant",
                    mode=mode,
                    content=final_content,
                )

                yield f"data: {json.dumps({'type': 'done', 'assistant_message': MessageSerializer(assistant_msg).data}, ensure_ascii=False)}\n\n"

            except Exception as exc:
                yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)}, ensure_ascii=False)}\n\n"

        response = StreamingHttpResponse(
            stream_generator(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

class ConversationMessagesView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        conv = Conversation.objects.get(id=pk, user=request.user)
        messages = conv.messages.order_by("created_at")
        return Response(MessageSerializer(messages, many=True).data)

class StudioMessageDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return Message.objects.get(
            id=pk,
            conversation__user=request.user,
            role="assistant",
            mode__in=["FLASHCARD", "QUIZ"],
        )

    def patch(self, request, pk):
        msg = self.get_object(request, pk)

        title = (request.data.get("title") or "").strip()
        if not title:
            return Response({"detail": "title is required"}, status=400)

        msg.title = title
        msg.save(update_fields=["title"])

        return Response(MessageSerializer(msg).data)

    def delete(self, request, pk):
        msg = self.get_object(request, pk)
        msg.delete()
        return Response(status=204)
