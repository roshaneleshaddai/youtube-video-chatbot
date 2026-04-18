# 🎓 VidChat – Interactive Learning from Video Content

VidChat is an AI-powered multimodal learning system that transforms passive video and document-based learning into an interactive experience. It processes educational videos and documents to generate summaries, quizzes, and enables conversational Q&A using Retrieval-Augmented Generation (RAG).

---

## 🔗 Project Resources

- 📄 **Project Report:**  
  https://1drv.ms/w/c/411c9b1b4b7e0494/IQDiJgR30TltQZOGuvx-X8pqARyRANEGZEJq6UaeQAyARt8?e=AK2hiD  

- 💻 **Mini Project (Colab - Mini 1 & Mini 2):**  
  https://colab.research.google.com/drive/1kDgSk1Wo3FpFzQrnuVaC8pGrNvbtpR6C?usp=sharing  

- 📊 **Final Presentation:**  
  https://1drv.ms/p/c/411c9b1b4b7e0494/IQCQKmK_76GwRrgeEVH1QKK2AeCyZK9HzTiapgJDnUQBnnM?e=gcE6fb  

---

## 🚀 Features

- 🎥 **Video Processing**
  - Extracts audio using Whisper (ASR)
  - Processes visual frames (code, diagrams, formulas)

- 🧠 **Multimodal Understanding**
  - Combines audio + visual data into a unified representation (MAT)

- 📄 **Document Support**
  - Upload PDFs, text files, code files, etc.

- 📝 **Smart Summarization**
  - Generates structured summaries including:
    - Code snippets
    - Formulas
    - Key concepts

- ❓ **Interactive Quiz Generation**
  - Auto-generated MCQs
  - Detailed explanations for answers

- 💬 **Conversational AI (RAG-based)**
  - Ask questions about video/document
  - Context-aware, grounded responses

- ⚡ **Efficient Retrieval**
  - Uses vector database (ChromaDB)
  - Semantic search with embeddings

---

## 🏗️ System Architecture

The system follows a modular pipeline:

1. **Decompose**
   - Extract audio and frames from video

2. **Process**
   - Audio → Whisper (ASR)
   - Frames → OCR / BLIP / pix2tex

3. **Fuse**
   - Combine into Multimodal-Augmented Transcript (MAT)

4. **Generate**
   - Summary
   - Quiz
   - Chat responses using RAG

---

## 🛠️ Tech Stack

### Backend
- Python
- FastAPI
- ChromaDB (Vector Database)
- Whisper (ASR)
- Transformers / BLIP / pix2tex
- Google Gemini API

### Frontend
- React + TypeScript
- Tailwind CSS
- Axios

### AI/ML
- Multimodal Processing
- Retrieval-Augmented Generation (RAG)
- Embeddings (semantic search)
  
---

## ⚙️ How It Works

1. User uploads a video URL or document  
2. System processes content into MAT  
3. Generates:
   - Summary
   - Quiz  
4. Indexes data into vector DB  
5. User interacts via chatbot  

---

## 📈 Results

- Significant improvement over unimodal systems  
- Better contextual understanding using multimodal fusion  
- Enhanced user engagement via interactive features  

---

## 🔮 Future Enhancements

- Personalized learning recommendations  
- Multi-language support  
- Real-time video processing  
- Advanced visual reasoning  

---

## 👨‍💻 Authors

- **M Eleshaddai Roshan**  
- **G Sreeja**

---

## 🏫 Institution

Department of Information Technology  
V R Siddhartha Engineering College  
(Autonomous, Affiliated to JNTU-K)

---

## 📜 License

This project is developed for academic purposes.

---

## ⭐ Acknowledgement

We thank our guide **Dr. S. Suhasini** and the faculty of IT department for their continuous support and guidance.

---
