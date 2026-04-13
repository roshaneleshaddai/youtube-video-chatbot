# Project Summary for Research Documentation

## Title

Multimodal Learning Assistant using Retrieval-Augmented Generation (RAG) for Video and Document Understanding

## Abstract

This project presents a multimodal educational assistant that processes YouTube videos and uploaded documents, then generates three learner-centered outputs: an automatic summary, an interactive multiple-choice quiz, and a contextual chatbot powered by Retrieval-Augmented Generation (RAG). The system converts input content into a unified analysis representation (MAT), indexes semantic chunks in ChromaDB, and uses Gemini-based language generation for content synthesis and question answering. A FastAPI backend coordinates ingestion, transformation, indexing, and generation, while a React frontend provides a tabbed user interface for learning interactions. The design emphasizes reproducibility and efficiency through deterministic IDs, cache reuse, and source-agnostic components.

## Problem Statement

Students consume educational content from multiple formats (videos, notes, PDFs, code files), but understanding, reviewing, and querying this content is time-consuming. Traditional tools do not combine:

1. automatic understanding of long-form content,
2. retrieval-grounded question answering,
3. and assessment-ready quiz generation,
   in one integrated workflow.

This project addresses that gap with a multimodal pipeline and a single learner interface.

## Objectives

1. Support both video and document inputs in one system.
2. Generate concise summaries for rapid comprehension.
3. Create quizzes for formative learning assessment.
4. Enable context-grounded conversational Q&A via RAG.
5. Improve runtime efficiency with caching and index reuse.

## System Architecture

The system has two major layers.

### Backend (FastAPI)

- API entry and middleware in [backend/main.py](backend/main.py)
- Video processing route in [backend/routers/video.py](backend/routers/video.py)
- Document processing route in [backend/routers/document.py](backend/routers/document.py)
- Chat route in [backend/routers/chat.py](backend/routers/chat.py)
- Video MAT pipeline in [backend/services/pipeline.py](backend/services/pipeline.py)
- Document-to-MAT conversion in [backend/services/document.py](backend/services/document.py)
- RAG indexing and retrieval in [backend/services/rag.py](backend/services/rag.py)
- LLM generation (summary/quiz/title/chat) in [backend/services/llm.py](backend/services/llm.py)

### Frontend (React + TypeScript)

- Main orchestration and source selection in [frontend/src/App.tsx](frontend/src/App.tsx)
- Chat UI in [frontend/src/components/ChatInterface.tsx](frontend/src/components/ChatInterface.tsx)
- Summary display in [frontend/src/components/GeneratedSummary.tsx](frontend/src/components/GeneratedSummary.tsx)
- Quiz parsing and interaction in [frontend/src/components/InteractiveQuiz.tsx](frontend/src/components/InteractiveQuiz.tsx)
- Markdown rendering in [frontend/src/components/MarkdownRenderer.tsx](frontend/src/components/MarkdownRenderer.tsx)

## End-to-End Workflow

1. User submits either a YouTube URL or an uploaded document.
2. Content is transformed into MAT (Multimodal Analysis Text).
3. MAT is chunked and embedded into ChromaDB.
4. The system generates:
   - a short title,
   - a structured summary,
   - a multiple-choice quiz (with explanations).
5. During chat, the query is embedded, relevant chunks are retrieved, and an answer is generated from retrieved context.
6. Results are shown in Summary, Quiz, and Chat tabs in the frontend.

## Key Technical Contributions

1. Unified multimodal pipeline for two source types with one downstream learning experience.
2. Deterministic content IDs (SHA-256 based) to support reproducibility and cache consistency.
3. MAT cache and index reuse to avoid repeated heavy processing.
4. Educational output design combining summarization, assessment, and retrieval-grounded tutoring.
5. Quiz explanation support for feedback after incorrect responses.

## Methods and Design Choices

1. Video decomposition:
   - Audio extracted from video.
   - Frames sampled at intervals.
   - Speech transcribed using Whisper.
   - Visual stream currently uses lightweight placeholders (extensible for OCR/CV models).
2. Document parsing:
   - Supports txt, md, csv, json, log, py, js, ts, and pdf.
3. Retrieval layer:
   - Recursive chunking strategy for MAT.
   - Embedding generation with model fallback support.
   - Top-k semantic retrieval filtered by content ID.
4. Generation layer:
   - Prompt templates for summary, quiz, title, and chat answering.
   - Model fallback chain for improved robustness.

## Technology Stack

### Backend dependencies

Defined in [backend/requirements.txt](backend/requirements.txt):

- fastapi, uvicorn, pydantic, python-multipart
- chromadb, langchain, langchain-text-splitters, langchain-google-genai
- google-generativeai
- numpy, opencv-python, yt-dlp, moviepy, pydub
- openai-whisper, python-dotenv, pypdf

### Frontend dependencies

Defined in [frontend/package.json](frontend/package.json):

- react, react-dom, typescript, vite
- tailwindcss, postcss, autoprefixer
- axios, lucide-react, react-markdown

## Current Evaluation Status

A demo evaluation module exists for quality scoring when API quota is unavailable:

- Script: [backend/demo_evaluation_mock.py](backend/demo_evaluation_mock.py)
- Results: [backend/evaluation_results/demo_results_mock.json](backend/evaluation_results/demo_results_mock.json)

Current mock statistics indicate:

- Mean overall score: 4.05 / 5.00
- Median overall score: 3.78 / 5.00
- Strongest criterion (mock run): relevance

Note: These are mock heuristic scores used for demonstration and pipeline validation.

## Limitations

1. Visual stream is currently placeholder-based and does not yet include full OCR/diagram understanding.
2. Quality depends on transcription accuracy and LLM output behavior.
3. Evaluation currently includes mock scoring; full real-model evaluation should be repeated after quota reset.
4. Some prompts can be further constrained to reduce variance in generated answers.

## Future Work

1. Integrate OCR and diagram/formula extraction for richer visual grounding.
2. Add source citations in chat answers for higher transparency.
3. Expand evaluation with human-judged datasets and benchmark metrics.
4. Add personalization and adaptive quiz difficulty.
5. Optimize latency with asynchronous/background task orchestration.

## Conclusion

The project demonstrates a practical and extensible multimodal RAG learning assistant that unifies content ingestion, summarization, assessment, and contextual tutoring in one platform. It is suitable as a research prototype for AI-assisted education and can be extended toward production-grade adaptive learning systems.
