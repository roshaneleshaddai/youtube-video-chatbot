import os
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-3.1-pro-preview")
FALLBACK_MODELS = os.getenv(
    "GEMINI_FALLBACK_MODELS",
    "models/gemini-3.1-pro-preview,models/gemini-3-pro-preview,models/gemini-3.1-flash-lite-preview,models/gemini-2.5-flash",
)
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "22000"))


def _model_candidates() -> list[str]:
    candidates = [DEFAULT_GEMINI_MODEL]
    for raw in FALLBACK_MODELS.split(","):
        model_name = raw.strip()
        if model_name and model_name not in candidates:
            candidates.append(model_name)
    return candidates


def _configure_genai() -> None:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    genai.configure(api_key=api_key)


def _trim_mat_text(mat_text: str) -> str:
    if not mat_text:
        return ""
    if len(mat_text) <= MAX_PROMPT_CHARS:
        return mat_text
    logger.warning(
        "MAT text too long for prompt budget | original_chars=%s | trimmed_chars=%s",
        len(mat_text),
        MAX_PROMPT_CHARS,
    )
    return mat_text[:MAX_PROMPT_CHARS]


def _generate_with_fallback(prompt: str, task_name: str) -> str:
    _configure_genai()
    last_error = ""
    for model_name in _model_candidates():
        try:
            logger.debug("LLM call start | task=%s | model=%s | prompt_chars=%s", task_name, model_name, len(prompt))
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = response.text if response and response.text else ""
            logger.info(
                "LLM call success | task=%s | model=%s | response_chars=%s",
                task_name,
                model_name,
                len(text),
            )
            return text
        except Exception as exc:
            last_error = str(exc)
            logger.warning("LLM call failed | task=%s | model=%s | error=%s", task_name, model_name, last_error)
            continue
    return (
        f"LLM Error: Could not generate {task_name}. "
        f"Tried models: {', '.join(_model_candidates())}. Last error: {last_error}"
    )


def generate_final_summary(mat_text: str) -> str:
    logger.debug("generate_final_summary start | mat_chars=%s", len(mat_text) if mat_text else 0)
    trimmed_mat = _trim_mat_text(mat_text)
    prompt = f"""
    You are an expert academic summarizer. The following is an augmented transcript of a lecture. It includes spoken words and visual events from slides.
    Each [VISUAL_EVENT] has:
    - [FRAME_TYPE]: The type of content ('text', 'diagram', 'formula', 'code').
    - [IMPORTANCE_SCORE]: A score from 0.0 to 1.0 indicating how important the visual is.
    - [CONTENT]: The information extracted from the visual. For formulas, it's in LaTeX format.

    Your task is to create a concise, well-structured summary. Pay close attention to visual events with a high IMPORTANCE_SCORE and accurately incorporate the key formulas, code snippets, and diagram descriptions into your summary.

    --- AUGMENTED TRANSCRIPT ---
    {trimmed_mat}
    --- END TRANSCRIPT ---

    Provide your final, comprehensive summary:
    """
    return _generate_with_fallback(prompt, "summary")

def generate_quiz(mat_text: str) -> str:
    logger.debug("generate_quiz start | mat_chars=%s", len(mat_text) if mat_text else 0)
    trimmed_mat = _trim_mat_text(mat_text)
    prompt = f"""
    You are an expert quiz creator for educational content. Based on the following augmented transcript of a lecture, generate a multiple-choice quiz that covers the key concepts presented.

    --- AUGMENTED TRANSCRIPT ---
    {trimmed_mat}
    --- END TRANSCRIPT ---

    Please adhere to the following strict formatting and content rules:
    1.  The quiz must have at least 5 multiple-choice questions.
    2.  The questions should be diverse, cover the entire range of topics in the transcript, and not be repetitive.
    3.  The questions must be directly answerable from the provided transcript.
    4.  Do not ask questions about the speaker or presenter. Focus only on the subject matter.
    5.  Ensure all options for a question are unique.
    6.  The question should not talk about the transcript.
    7.  Include a brief explanation for the correct answer so the app can show it after a wrong attempt.

    Format each question exactly as follows:
    1. Question?
       a) Option 1
       b) Option 2
       c) Option 3
       d) Option 4
    Answer: a
     Explanation: reason why option a is correct and it should not mention about the transcript .

     Note: For the answer, provide ONLY the letter (a, b, c, or d) without any additional text. Use a newline after the answer. Keep the explanation concise and directly tied to the correct option.

    Begin the quiz now:
    """
    return _generate_with_fallback(prompt, "quiz")

def generate_rag_response(query: str, context: str) -> str:
    """Generates an answer to the query using the retrieved context."""
    logger.debug("generate_rag_response start | query_len=%s | context_chars=%s", len(query), len(context) if context else 0)
    if not context:
        return "I'm sorry, I don't have enough context from the analyzed content to answer that question."

    prompt = f"""
    You are VidChat, a specialized AI assistant designed to help students by answering questions about analyzed educational content (video or document). Your primary directive is to answer questions using ONLY the information provided in the 'CONTEXT' section below.

    **Response Style:**
    - **No Mention of Source:** Do not use phrases like "According to the context," "The transcript mentions," or "Based on the provided information." Act as if you know the information directly.
    - **Conversational and Helpful:** Answer like a knowledgeable tutor, not a formal lecturer.

    --- TASK ---
    1. Carefully analyze the 'Student Question' and the 'CONTEXT'.
    2. **If the answer is NOT in the CONTEXT:** You MUST start your response with the exact phrase "The video doesn't have the content of what you have asked but in general," and then provide a brief, general explanation of the topic and search for the youtube videos related to the topic and give them as suggestions.

    --- CONTEXT ---
    {context}
    
    --- STUDENT QUESTION ---
    {query}
    """
    return _generate_with_fallback(prompt, "answer")

def generate_title(mat_text: str) -> str:
    logger.debug("generate_title start | mat_chars=%s", len(mat_text) if mat_text else 0)
    trimmed_mat = _trim_mat_text(mat_text)
    prompt = f"""
    You are an expert at creating concise, catchy, and accurate titles for educational videos. 
    Based on the following augmented transcript of a lecture, generate a short title (maximum 6 words) that captures the main topic.

    --- AUGMENTED TRANSCRIPT ---
    {trimmed_mat}
    --- END TRANSCRIPT ---

    Provide ONLY the title text, with no quotes, formatting, or extra words:
    """
    return _generate_with_fallback(prompt, "title").strip()
