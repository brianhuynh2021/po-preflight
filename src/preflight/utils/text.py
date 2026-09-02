from __future__ import annotations

import re
import unicodedata


def normalize_vietnamese_name(text: str) -> str:
    """Normalize company / customer name: remove accents, lowercase, strip legal entity types and punctuation."""
    if not text:
        return ""

    # 1. Normalize NFD and remove diacritical marks
    nfkd = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    stripped = stripped.replace("đ", "d").replace("Đ", "D")

    # 2. Lowercase
    clean = stripped.lower()

    # 3. Strip legal entity prefixes / suffixes (Vietnamese & English)
    entity_pattern = r"\b(cong ty|cty|tnhh|cp|co|ltd|co\.|ltd\.|jsc|group|corp|corporation|tap doan|chi nhanh|doanh nghiep|dn|mtv)\b"
    clean = re.sub(entity_pattern, " ", clean)

    # 4. Remove special characters and punctuation
    clean = re.sub(r"[^\w\s]", " ", clean)

    # 5. Collapse multiple spaces
    return " ".join(clean.split()).strip()
