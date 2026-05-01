from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from rest_framework.test import APIClient

from .models import Material, MaterialChunk, Conversation, Message
from .engine import generate_response, _prepare_chunk_record


User = get_user_model()


class ChatbotEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

        self.material = Material.objects.create(
            user=self.user,
            title="Networking Basics",
            file=SimpleUploadedFile(
                "networking.txt",
                b"TCP is Transmission Control Protocol.",
                content_type="text/plain",
            ),
            file_type="txt",
            status="DONE",
            progress=100,
        )

        self.chunk = MaterialChunk.objects.create(
            material=self.material,
            order=1,
            text=(
                "Networking Basics\n"
                "TCP stands for Transmission Control Protocol.\n"
                "The OSI Model has 7 layers.\n"
                "Machine learning includes supervised and unsupervised learning."
            ),
            embedding=None,
        )

        self.retrieved_chunks = [
            {
                "chunk": self.chunk,
                "score": 999.0,
                "rerank_score": 999.0,
            }
        ]

    @patch("chatbot.engine.generate_llm_answer")
    def test_flashcard_parser_creates_items(self, mock_llm):
        mock_llm.return_value = """
### Flashcards

- Q: What does TCP stand for?
A: Transmission Control Protocol

- Q: OSI Model
A: A 7-layer model used to understand network communication.

- Q: What is Machine Learning?
A: A field that allows systems to learn from data.
"""

        result = generate_response(
            mode="FLASHCARD",
            user_message="generate flashcard",
            retrieved_chunks=self.retrieved_chunks,
            material_id=self.material.id,
            conversation_history=None,
        )

        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 3)

        self.assertEqual(
            result["items"][0]["front"],
            "What does TCP stand for?"
        )
        self.assertEqual(
            result["items"][0]["back"],
            "Transmission Control Protocol"
        )

        # Test case: nếu LLM trả keyword "OSI Model",
        # backend phải tự đổi thành câu hỏi.
        self.assertEqual(
            result["items"][1]["front"],
            "What is OSI Model?"
        )

    @patch("chatbot.engine.generate_llm_answer")
    def test_quiz_parser_creates_mcq_items(self, mock_llm):
        mock_llm.return_value = """
### Quiz Questions:

Q: What does TCP stand for?
A. Transfer Control Program
B. Transmission Control Protocol
C. Transport Channel Process
D. Terminal Connection Protocol
Answer: B

Q: How many layers are in the OSI Model?
A. 4
B. 5
C. 7
D. 9
Answer: C
"""

        result = generate_response(
            mode="QUIZ",
            user_message="generate quiz",
            retrieved_chunks=self.retrieved_chunks,
            material_id=self.material.id,
            conversation_history=None,
        )

        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 2)

        first = result["items"][0]
        self.assertEqual(first["type"], "mcq")
        self.assertEqual(first["question"], "What does TCP stand for?")
        self.assertEqual(len(first["choices"]), 4)
        self.assertEqual(first["answer_index"], 1)

    def test_out_of_scope_flashcard_returns_empty_items(self):
        result = generate_response(
            mode="FLASHCARD",
            user_message="generate flashcard",
            retrieved_chunks=[],
            material_id=self.material.id,
            conversation_history=None,
        )

        self.assertEqual(result["items"], [])
        self.assertIn("message", result)

    def test_out_of_scope_quiz_returns_empty_items(self):
        result = generate_response(
            mode="QUIZ",
            user_message="generate quiz",
            retrieved_chunks=[],
            material_id=self.material.id,
            conversation_history=None,
        )

        self.assertEqual(result["items"], [])
        self.assertIn("message", result)


class ChatbotAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="apiuser",
            password="testpass123"
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.material = Material.objects.create(
            user=self.user,
            title="Networking Basics",
            file=SimpleUploadedFile(
                "networking.txt",
                b"TCP is Transmission Control Protocol.",
                content_type="text/plain",
            ),
            file_type="txt",
            status="DONE",
            progress=100,
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            material=self.material,
            title="Networking Basics",
        )

    @patch("chatbot.views.generate_response")
    @patch("chatbot.views.retrieve_for_level2_chat")
    def test_chat_api_creates_flashcard_message(self, mock_retrieve, mock_generate):
        mock_retrieve.return_value = []
        mock_generate.return_value = {
            "items": [
                {
                    "front": "What does TCP stand for?",
                    "back": "Transmission Control Protocol",
                    "tags": ["auto"],
                }
            ]
        }

        response = self.client.post(
            "/api/chat/",
            {
                "conversation_id": self.conversation.id,
                "mode": "FLASHCARD",
                "message": "generate flashcard",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("user_message", data)
        self.assertIn("assistant_message", data)

        assistant = data["assistant_message"]
        self.assertEqual(assistant["mode"], "FLASHCARD")
        self.assertEqual(assistant["title"], "Flash card 1")
        self.assertEqual(len(assistant["content"]["items"]), 1)

        self.assertEqual(
            Message.objects.filter(
                conversation=self.conversation,
                role="assistant",
                mode="FLASHCARD",
            ).count(),
            1,
        )

    @patch("chatbot.views.generate_response")
    @patch("chatbot.views.retrieve_for_level2_chat")
    def test_chat_api_creates_quiz_message(self, mock_retrieve, mock_generate):
        mock_retrieve.return_value = []
        mock_generate.return_value = {
            "items": [
                {
                    "type": "mcq",
                    "question": "What does TCP stand for?",
                    "choices": [
                        "Transfer Control Program",
                        "Transmission Control Protocol",
                        "Transport Channel Process",
                        "Terminal Connection Protocol",
                    ],
                    "answer_index": 1,
                }
            ]
        }

        response = self.client.post(
            "/api/chat/",
            {
                "conversation_id": self.conversation.id,
                "mode": "QUIZ",
                "message": "generate quiz",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        assistant = response.json()["assistant_message"]
        self.assertEqual(assistant["mode"], "QUIZ")
        self.assertEqual(assistant["title"], "Quiz 1")
        self.assertEqual(len(assistant["content"]["items"]), 1)