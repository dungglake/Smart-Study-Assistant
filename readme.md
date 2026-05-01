## Project Overview

Smart Study Assistant is a web-based learning support system designed to help students manage their study process more effectively. The system allows users to upload study materials and interact with them through an AI-powered chatbot. Based on the uploaded documents, the application can generate summaries, answer questions, create flashcards, and generate quiz questions to support active learning.

In addition, the project includes a study planner feature that helps students organize their study schedule based on subjects, tasks, and available study time.

## Main Features

- User registration and login
- Upload study materials such as PDF, TXT, DOCX, and MD files
- Chat with uploaded documents using AI
- Generate flashcards from study materials
- Generate quiz questions from study materials
- Manage study sources
- Create and manage study schedules using the planner
- Run backend unit tests for chatbot and system features

## Requirements

Before running this project, install:

- Python 3.10+ (or latest)
- Node.js 18+ (or latest)
- Ollama

---

## 1. Clone Project

```bash
git clone https://github.com/dungglake/Smart-Study-Assistant
cd SMARTSTUDYASSISTANT
```

---

## 2. Install and Run Backend

Open a terminal and run:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # Mac/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend will run at:

```bash
http://127.0.0.1:8000
```

---

## 3. Install and Run Ollama

Open a new terminal and run:

```bash
ollama pull llama3
ollama pull nomic-embed-text
ollama serve
```

To check whether Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

---

## 4. Install and Run Frontend

Open another terminal and run:

```bash
cd frontend/zentask-dashboard
npm install
npm run dev
```

Frontend will run at (This is where you will test the project's functionality):

```bash
http://localhost:5173
```


## Notes

Make sure the backend, frontend, and Ollama are running at the same time when testing planning schedule, AI features such as chat, quiz generation, and flashcard generation.
And you need to register after log in. 
