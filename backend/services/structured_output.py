"""核心功能：提取模型文本中的 JSON 对象片段，兼容代码块、思维标签与额外前后缀。"""

import re


def extract_json_object_text(raw_output: str) -> str:
    stripped = raw_output.strip()
    if not stripped:
        raise ValueError("Model output was empty.")

    stripped = re.sub(r"^\s*</think>\s*", "", stripped, flags=re.IGNORECASE)

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)

    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        return stripped[first_brace : last_brace + 1]

    return stripped
