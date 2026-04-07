import os
from turtle import mode
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Material, MaterialChunk, Conversation, Message
from .serializers import MaterialSerializer, ConversationSerializer, ChatRequestSerializer
from .utils import extract_text_from_file, chunk_text
from .engine import retrieve_top_chunks, generate_response


class MaterialListCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Material.objects.filter(user=request.user).order_by("-created_at")
        return Response(MaterialSerializer(qs, many=True).data)

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

        try:
            path = material.file.path
            text = extract_text_from_file(path, ext)
            material.progress = 30
            material.save(update_fields=["progress"])

            chunks = chunk_text(text, max_chars=1200)
            objs = [MaterialChunk(material=material, order=i, text=ch) for i, ch in enumerate(chunks, start=1)]
            MaterialChunk.objects.bulk_create(objs)

            material.status = "DONE"
            material.progress = 100
            material.save(update_fields=["status", "progress"])
        except Exception as e:
            material.status = "FAILED"
            material.save(update_fields=["status"])
            return Response({"detail": f"processing failed: {str(e)}"}, status=500)

        return Response({"material_id": material.id, "status": material.status}, status=201)


class MaterialDetailView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        material = Material.objects.get(pk=pk, user=request.user)
        return Response(MaterialSerializer(material).data)


class ConversationCreateView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        material_id = serializer.validated_data["material"].id
        material = Material.objects.get(id=material_id, user=request.user)
        conv = Conversation.objects.create(user=request.user, material=material)

        return Response({"conversation_id": conv.id}, status=201)


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

        Message.objects.create(
            conversation=conv,
            role="user",
            mode=mode,
            content={"text": user_message}
        )

        retrieved_chunks = retrieve_top_chunks(conv.material_id, user_message, k=4)
        content = generate_response(mode, user_message, retrieved_chunks)

        Message.objects.create(
            conversation=conv,
            role="assistant",
            mode=mode,
            content=content
        )

        return Response({"role": "assistant", "mode": mode, "content": content}, status=200)