# StoryNest - AI Kids Story Generator

StoryNest is an AI-powered platform that automatically generates engaging children's stories complete with morals, age-appropriate content, image prompts, and social media captions. It features an automated agentic pipeline in the backend and a beautiful modern frontend to view and manage these stories.

## Features

- **Automated Story Generation**: Uses an advanced LLM pipeline (LangGraph + LangChain) to write kids stories dynamically.
- **Admin Approval Workflow**: An admin dashboard allows reviewing, approving, or rejecting generated stories with feedback, triggering automated regeneration if needed.
- **Background Task Scheduling**: Automatically schedules and runs story generation tasks.
- **Modern UI**: A responsive, beautifully crafted Next.js frontend with dark mode support.
- **Social Media Ready**: Generates tailored captions for Facebook and Instagram for every story.

## Tech Stack

### Backend
- **Framework**: FastAPI
- **AI & Automation**: LangGraph, LangChain, OpenAI
- **Scheduling**: APScheduler
- **Database**: Local JSON Storage (for POC)

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Language**: TypeScript

---

## 🚀 Getting Started

Follow these instructions to run the project locally.

### Prerequisites
- Python 3.10+
- Node.js 18+
- API Keys configured in `backend/.env` (`OPENAI_API_KEY=your_key` and `GROQ_API_KEY=your_key`)
- Dependencies installed in both frontend (`npm install`) and backend (`pip install -r requirements.txt`)

> **Note**: Start Terminal 2 first, wait for `Application startup complete`, then start Terminal 1. 🚀

***

### Terminal 1 — Frontend (Next.js)
```bash
cd /Volumes/D_Drive/WBS-AI/kids-story-poc/frontend
npm run dev
```
🟢 Runs at: **http://localhost:3000**

***

### Terminal 2 — Backend (FastAPI)
```bash
cd /Volumes/D_Drive/WBS-AI/kids-story-poc/backend
source venv/bin/activate
python -m uvicorn main:app --reload --port 8000
```
🟢 Runs at: **http://127.0.0.1:8000**

***

### Terminal 3 — Trigger Story (when needed)
```bash
curl -X POST http://127.0.0.1:8000/admin/generate
```

---

## 📖 Application Structure

### Public View (`http://localhost:3000/`)
- View a feed of all published and approved stories.
- Read individual stories with their beautiful cover images, morals, and age tags.

### Admin Dashboard (`http://localhost:3000/admin`)
- Manage all stories in the database.
- Manually trigger the generation of a new story (up to 3 per day).
- **Review Workflow**: Review pending stories and either **Publish** them to the public view or **Reject** them. If rejected, the admin can provide feedback, which tells the AI agent to automatically regenerate a new version of the story based on the critique.

---

## 🛠️ Environment Variables Reference

**Backend (`backend/.env`)**
- `OPENAI_API_KEY`: Your OpenAI API key required to generate stories via LangChain.
- `GROQ_API_KEY`: Your Groq API key used for accelerated inference.

## Acknowledgments
Built as a Proof of Concept (POC) to demonstrate LLM agentic workflows and automated content generation.
