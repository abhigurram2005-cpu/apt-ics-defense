"""
chat_engine.py

Provides two public functions:

    get_response(user_query, system_prompt, chat_history) -> str
        Sends a query to Gemini 1.5 Flash while preserving multi-turn
        conversation history.

    parse_optional_pdf(uploaded_file) -> str
        Extracts all text from an uploaded PDF using PyMuPDF (fitz) and
        returns it as a plain string ready to be appended to the KB.

Dependencies
------------
    pip install google-generativeai pymupdf
"""

from __future__ import annotations

import io
import logging
import os
from typing import Any

import fitz  # type: ignore # PyMuPDF
from dotenv import load_dotenv # type: ignore

import google.generativeai as genai # type: ignore
from google.generativeai.types import GenerationConfig # type: ignore

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SDK initialisation
# ---------------------------------------------------------------------------
# Load variables from .env (silently ignored if the file doesn't exist so
# the module still works when secrets are injected via the real environment).
load_dotenv()

_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
if not _API_KEY:
    logger.warning(
        "GEMINI_API_KEY environment variable is not set. "
        "Calls to get_response() will raise an AuthenticationError."
    )

genai.configure(api_key=_API_KEY)

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
_MODEL_NAME = "gemini-1.5-flash"

_GENERATION_CONFIG = GenerationConfig(
    temperature=0.2,        # low temperature → consistent, policy-grounded answers
    top_p=0.95,
    top_k=40,
    max_output_tokens=1024,
)

_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_model(system_prompt: str) -> genai.GenerativeModel:
    """
    Instantiate a GenerativeModel with the given system instruction.

    The model is created fresh for each logical conversation so that
    different companies / system prompts never bleed into each other.
    """
    return genai.GenerativeModel(
        model_name=_MODEL_NAME,
        generation_config=_GENERATION_CONFIG,
        safety_settings=_SAFETY_SETTINGS,
        system_instruction=system_prompt,
    )


def _history_to_sdk_format(chat_history: list[dict[str, str]]) -> list[dict[str, Any]]:
    """
    Convert a plain list of {"role": ..., "content": ...} dicts into the
    format expected by the Gemini SDK:
        [{"role": "user" | "model", "parts": ["text..."]}]

    The SDK uses "model" for assistant turns (not "assistant").
    """
    sdk_history: list[dict[str, Any]] = []
    for turn in chat_history:
        role = turn.get("role", "").lower()
        content = turn.get("content", "")
        # Normalise "assistant" → "model"
        if role == "assistant":
            role = "model"
        if role not in {"user", "model"}:
            logger.debug("Skipping unknown role '%s' in chat history.", role)
            continue
        sdk_history.append({"role": role, "parts": [content]})
    return sdk_history


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_response(
    user_query: str,
    system_prompt: str,
    chat_history: list[dict[str, str]],
) -> str:
    """
    Send *user_query* to Gemini 1.5 Flash and return the model's text reply.

    The function is stateless from the caller's perspective: pass the full
    conversation history each time and it will be replayed to the model so
    that context is preserved across turns.

    Parameters
    ----------
    user_query:
        The latest message from the user.
    system_prompt:
        The system instruction built by ``build_system_prompt()``.  Passed
        as the model's ``system_instruction`` so it is not part of the
        conversational history and cannot be overridden by the user.
    chat_history:
        All previous turns in the conversation, each represented as a dict::

            {"role": "user" | "assistant" | "model", "content": "<text>"}

        Pass an empty list ``[]`` to start a fresh conversation.

    Returns
    -------
    str
        The model's response text.

    Raises
    ------
    ValueError
        If *user_query* or *system_prompt* is empty.
    google.api_core.exceptions.GoogleAPIError
        On network or API-level failures (authentication, quota, etc.).
    """
    if not user_query or not user_query.strip():
        raise ValueError("user_query must be a non-empty string.")
    if not system_prompt or not system_prompt.strip():
        raise ValueError("system_prompt must be a non-empty string.")

    model = _build_model(system_prompt)

    # Seed the chat session with prior history so the model has full context.
    sdk_history = _history_to_sdk_format(chat_history)
    chat_session = model.start_chat(history=sdk_history)

    logger.debug("Sending query to %s (history turns: %d)", _MODEL_NAME, len(sdk_history))

    response = chat_session.send_message(user_query.strip())

    # Extract text safely — handle blocked responses gracefully.
    try:
        reply = response.text
    except ValueError:
        # response.text raises ValueError when the response was blocked by
        # safety filters and contains no usable candidates.
        finish_reason = (
            response.candidates[0].finish_reason.name
            if response.candidates
            else "UNKNOWN"
        )
        logger.warning("Response blocked by safety filters. Finish reason: %s", finish_reason)
        reply = (
            "I'm sorry, I wasn't able to generate a response to that query. "
            "Please rephrase your question or contact HR directly."
        )

    return reply


def parse_optional_pdf(uploaded_file: Any) -> str:
    """
    Extract all text from an uploaded PDF file using PyMuPDF (fitz).

    The function accepts several common "uploaded file" shapes:

    * A ``bytes`` or ``bytearray`` object.
    * Any file-like object with a ``.read()`` method
      (e.g. ``io.BytesIO``, a Streamlit ``UploadedFile``,
      or a standard ``open(..., "rb")`` handle).
    * A ``str`` or ``pathlib.Path`` pointing to a file on disk.

    Parameters
    ----------
    uploaded_file:
        The PDF source in any of the forms described above.
        Pass ``None`` to indicate no file was uploaded — the function
        returns an empty string in that case so callers can safely do::

            extra = parse_optional_pdf(uploaded_file)
            full_kb = base_kb + ("\\n\\n" + extra if extra else "")

    Returns
    -------
    str
        Concatenated plain text extracted from every page of the PDF,
        with pages separated by a form-feed character (``\\f``).
        Returns ``""`` if *uploaded_file* is ``None`` or the PDF has no
        extractable text.

    Raises
    ------
    ValueError
        If the supplied object is not a recognised type.
    fitz.FileDataError
        If the bytes / file is not a valid PDF.
    OSError
        If a file path is supplied but cannot be opened.
    """
    if uploaded_file is None:
        return ""

    # --- Resolve to raw bytes ------------------------------------------------
    if isinstance(uploaded_file, (bytes, bytearray)):
        pdf_bytes = bytes(uploaded_file)

    elif hasattr(uploaded_file, "read"):
        # File-like: Streamlit UploadedFile, io.BytesIO, open() handle, etc.
        # Seek to the beginning in case the caller already read part of it.
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()

    elif isinstance(uploaded_file, (str, os.PathLike)):
        path = str(uploaded_file)
        with open(path, "rb") as fh:
            pdf_bytes = fh.read()

    else:
        raise ValueError(
            f"Unsupported type for uploaded_file: {type(uploaded_file)}. "
            "Expected bytes, a file-like object, or a file path string."
        )

    # --- Extract text with PyMuPDF -------------------------------------------
    pages: list[str] = []
    with fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf") as doc:
        logger.debug("PDF opened: %d pages, title=%r", doc.page_count, doc.metadata.get("title"))
        for page_index, page in enumerate(doc):
            text = page.get_text("text")   # plain UTF-8 text
            if text.strip():
                pages.append(text)
            else:
                logger.debug("Page %d yielded no extractable text (may be image-only).", page_index)

    extracted = "\f".join(pages)   # \f = form-feed, standard page separator
    logger.debug("PDF extraction complete: %d chars across %d pages.", len(extracted), len(pages))
    return extracted