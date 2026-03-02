"""
PDF Highlighter Tool — highlights cited paragraphs in the SDAIA PDF.

Uses ARA-Reranker-V1 (Arabic cross-encoder) to match answer points
to PDF paragraphs with state-of-the-art semantic accuracy.

Pipeline:
  1. Parse the compliance answer into (point_text, page_number) pairs
  2. For each cited page, extract paragraphs via vertical-gap grouping
  3. Score each (answer_point, paragraph) pair with the cross-encoder
  4. Highlight the best-matching paragraph (full multi-line highlight)
"""
import fitz  # PyMuPDF
import re
import os
import unicodedata
import logging
import numpy as np
from math import exp
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(BASE_DIR, "data", "ai-principles.pdf")
OUTPUT_DIR = os.path.join(BASE_DIR, "data")

PARAGRAPH_GAP_THRESHOLD = 5.0
RERANKER_THRESHOLD = 0.3

_cross_encoder = None


# ── Cross-Encoder (lazy singleton) ────────────────────────────────────

def _get_model():
    """Load ARA-Reranker-V1 on first call, reuse thereafter."""
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder
        logger.warning("[HIGHLIGHT] Loading ARA-Reranker-V1 cross-encoder...")
        _cross_encoder = CrossEncoder(
            "Omartificial-Intelligence-Space/ARA-Reranker-V1"
        )
        logger.warning("[HIGHLIGHT] Cross-encoder loaded.")
    return _cross_encoder


def _sigmoid(x: float) -> float:
    """Convert raw logit to 0-1 probability."""
    return 1.0 / (1.0 + exp(-x))


# ── Arabic normalisation ─────────────────────────────────────────────

def _normalize_arabic(text: str) -> str:
    """Collapse Arabic encoding variants for display/logging."""
    n = unicodedata.normalize('NFKC', text)
    n = re.sub(
        r'[\u0610-\u061A\u064B-\u065F\u0670'
        r'\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]',
        '', n
    )
    n = re.sub(r'[آأإٱ]', 'ا', n)
    n = n.replace('ة', 'ه')
    n = n.replace('ى', 'ي')
    n = re.sub(r'\s+', ' ', n).strip()
    return n


# ── Answer parsing ────────────────────────────────────────────────────

def _parse_answer_points(answer_text: str) -> list:
    """
    Split a numbered compliance answer into (point_text, page_number) pairs.

    Handles formats like:
      1. some text (صفحة 16)
      2. some text (صفحة 17)
    or:
      - some text (صفحة 16)
    """
    points = []

    parts = re.split(r'(?:^|\n)\s*(?:\d+[.\-)]|[•\-]\s*\d*)', answer_text)

    if len(parts) <= 1:
        parts = re.split(r'\(صفحة\s*\d+\)', answer_text)

    for part in parts:
        part = part.strip()
        if len(part) < 10:
            continue

        page_matches = re.findall(r'صفحة\s*(\d+)', part)
        if not page_matches:
            idx = answer_text.find(part[:30])
            if idx >= 0:
                nearby = answer_text[max(0, idx - 20):idx + len(part) + 20]
                page_matches = re.findall(r'صفحة\s*(\d+)', nearby)

        for page_str in page_matches:
            points.append((part, int(page_str)))

        if not page_matches:
            logger.warning(f"[HIGHLIGHT] No page ref for point: {part[:50]}")

    return points


# ── Page structure extraction ─────────────────────────────────────────

def _get_page_lines(page) -> list:
    """Extract all text lines with bounding boxes, sorted top-to-bottom."""
    td = page.get_text("dict")
    lines = []
    for block in td.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            lt = "".join(s.get("text", "") for s in line.get("spans", []))
            if lt.strip():
                lines.append({"text": lt, "bbox": line["bbox"]})
    lines.sort(key=lambda l: l["bbox"][1])
    return lines


def _group_into_paragraphs(lines: list) -> list:
    """
    Group consecutive lines into paragraphs using vertical-gap analysis.
    Within an item lines overlap (gap < 5 px); between items gap ~ 10 px.
    """
    if not lines:
        return []
    paras = [[lines[0]]]
    for i in range(1, len(lines)):
        gap = lines[i]["bbox"][1] - lines[i - 1]["bbox"][3]
        if gap > PARAGRAPH_GAP_THRESHOLD:
            paras.append([lines[i]])
        else:
            paras[-1].append(lines[i])
    return paras


# ── Highlighting ──────────────────────────────────────────────────────

def _highlight_paragraph(page, para_lines: list) -> int:
    """Add a yellow highlight annotation over every line of a paragraph."""
    count = 0
    for li in para_lines:
        rect = fitz.Rect(li["bbox"])
        if rect.is_empty or rect.is_infinite:
            continue
        try:
            annot = page.add_highlight_annot(rect)
            annot.set_colors(stroke=(1, 1, 0))
            annot.update()
            count += 1
        except Exception:
            continue
    return count


# ── Public tool function ──────────────────────────────────────────────

def highlight_sdaia_pdf(answer_text: str) -> str:
    """
    Highlight the paragraphs cited in a compliance answer inside the SDAIA PDF.

    Uses ARA-Reranker-V1 cross-encoder to score each (answer_point, paragraph)
    pair and highlights the best-matching paragraph per point.

    Args:
        answer_text: The ANSWER section from the compliance agent, containing
                     numbered points with (صفحة N) page citations.
    Returns:
        Success message with filename, or error description.
    """
    if not answer_text or len(answer_text.strip()) < 20:
        return "ERROR: answer_text is too short or empty"

    if not os.path.exists(PDF_PATH):
        return f"ERROR: PDF not found at {PDF_PATH}"

    points = _parse_answer_points(answer_text)
    if not points:
        return "ERROR: Could not extract any points with page citations from the answer"

    model = _get_model()

    doc = fitz.open(PDF_PATH)
    total_highlights = 0
    highlighted_pages = []
    page_para_cache = {}

    for point_text, page_num in points:
        page_index = page_num - 1
        if not (0 <= page_index < len(doc)):
            continue

        if page_num not in page_para_cache:
            page = doc[page_index]
            lines = _get_page_lines(page)
            paras = _group_into_paragraphs(lines)
            page_para_cache[page_num] = (page, paras)

        page, paras = page_para_cache[page_num]

        candidate_paras = [
            p for p in paras
            if len(" ".join(li["text"] for li in p)) > 20
        ]
        if not candidate_paras:
            continue

        # Build (query, passage) pairs for the cross-encoder
        para_texts = [" ".join(li["text"] for li in p) for p in candidate_paras]
        pairs = [(point_text, pt) for pt in para_texts]

        raw_scores = model.predict(pairs)
        scores = np.array([_sigmoid(s) for s in raw_scores])

        best_idx = int(scores.argmax())
        best_score = float(scores[best_idx])

        if best_score >= RERANKER_THRESHOLD:
            best_para = candidate_paras[best_idx]
            count = _highlight_paragraph(page, best_para)
            if count > 0:
                total_highlights += count
                highlighted_pages.append(page_num)
                logger.warning(
                    f"[HIGHLIGHT] p{page_num} OK ({best_score:.2f}): "
                    f"{para_texts[best_idx][:50]}"
                )
        else:
            logger.warning(
                f"[HIGHLIGHT] p{page_num} MISS ({best_score:.2f}): "
                f"{point_text[:50]}"
            )

    if total_highlights == 0:
        doc.close()
        return "ERROR: Could not match any answer points to PDF paragraphs"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"sdaia_highlighted_{timestamp}.pdf"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    doc.save(output_path)
    doc.close()

    pages_str = ", ".join(str(p) for p in sorted(set(highlighted_pages)))
    return (
        f"Highlighted PDF created successfully!\n"
        f"File: {output_filename}\n"
        f"Pages: {pages_str}\n"
        f"Highlights: {total_highlights} lines\n"
        f"Location: data folder"
    )
