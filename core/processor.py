"""
Upstage Document Parse Logic.
Parse PDFs, memos into structured content for downstream agent.
"""

from pathlib import Path
from typing import Union

from langchain_upstage import UpstageDocumentParseLoader


def process_documents(files: list[Union[str, Path]]) -> str:
    """
    Load multiple documents via Upstage Document Parse and return concatenated text.

    Args:
        files: List of file paths (str or Path). Supported: PDF, images, etc.

    Returns:
        Concatenated text (HTML output from parser) from all documents.

    Raises:
        FileNotFoundError: If any path does not exist.
        ValueError: If files list is empty or loader fails.
    """
    if not files:
        raise ValueError("files must be a non-empty list of file paths")

    all_parts: list[str] = []

    for f in files:
        path = Path(f) if not isinstance(f, Path) else f
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        try:
            loader = UpstageDocumentParseLoader(
                str(path),
                split="none",
                ocr="force",
                output_format="html",
            )
            docs = loader.load()
        except Exception as e:
            raise ValueError(f"Failed to load document {path}: {e}") from e

        for doc in docs:
            content = getattr(doc, "page_content", "") or ""
            if content.strip():
                all_parts.append(content.strip())

    if not all_parts:
        raise ValueError("No content extracted from any of the given files")

    return "\n\n".join(all_parts)
