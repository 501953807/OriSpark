"""代码抄袭检测服务 (P2.3.10).

使用 AST 指纹 + 树结构比较进行简化代码相似度检测:
- 基于 Python tokenize 提取结构指纹
- 使用序列化 AST 骨架对比
- 支持常见脚本语言的字符串指纹比对
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class CodeFingerprint:
    """代码指纹."""
    file_path: str
    normalized_tokens: list[str] = field(default_factory=list)
    structure_hash: str = ""
    keyword_vector: dict[str, int] = field(default_factory=dict)
    line_count: int = 0
    comment_ratio: float = 0.0


@dataclass
class CodeSimilarityResult:
    """代码相似度结果."""
    file_a: str
    file_b: str
    similarity: float  # 0-100
    structure_similarity: float = 0.0
    keyword_similarity: float = 0.0
    is_mock: bool = False
    message: str = ""


# Python 关键字集合
PYTHON_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield",
}

# 常见标识符正则 (可用于 Python/JS/TS/Java/C)
IDENTIFIER_RE = re.compile(r'[a-zA-Z_]\w*')
COMMENT_RE_PYTHON = re.compile(r'#[^\n]*')
COMMENT_RE_CSLASH = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/')


def tokenize_python_code(source: str) -> list[str]:
    """Tokenize Python 源代码并归一化.

    归一化规则:
    - 忽略注释和空行
    - 替换字符串/数字字面量为占位符
    - 保留关键字和运算符

    Returns:
        归一化 token 列表.
    """
    import tokenize
    import io

    try:
        tokens = []
        reader = io.StringIO(source)
        for tok in tokenize.generate_tokens(reader.readline):
            tok_type, tok_string, _, _, _ = tok
            # 跳过注释、换行、编码声明
            if tok_type in (tokenize.COMMENT, tokenize.NL, tokenize.ENCODING):
                continue
            if tok_type == tokenize.STRING:
                tokens.append("<STR>")
            elif tok_type == tokenize.NUMBER:
                tokens.append("<NUM>")
            elif tok_type == tokenize.NEWLINE:
                tokens.append("<NL>")
            elif tok_type == tokenize.INDENT:
                tokens.append("<INDENT>")
            elif tok_type == tokenize.DEDENT:
                tokens.append("<DEDENT>")
            elif tok_type == tokenize.NAME:
                tokens.append(tok_string)
            else:
                tokens.append(tok_string)
        return tokens
    except tokenize.TokenError:
        # fallback: 简单的字符串 tokenize
        return _simple_tokenize(source)


def _simple_tokenize(source: str) -> list[str]:
    """简单 tokenize - 当标准库 tokenize 失败时的 fallback."""
    tokens = []
    # 移除注释
    source = COMMENT_RE_PYTHON.sub('', source)
    # 分割单词
    for word in IDENTIFIER_RE.findall(source):
        if word in PYTHON_KEYWORDS:
            tokens.append(word)
        else:
            tokens.append("<ID>")
    return tokens


def tokenize_generic_code(source: str, language: str = "python") -> list[str]:
    """通用代码 tokenize.

    支持: python, javascript, typescript.
    """
    if language in ("python", "py"):
        return tokenize_python_code(source)
    else:
        # JS/TS/其他: 简单归一化
        source = COMMENT_RE_CSLASH.sub('', source)
        tokens = []
        for word in IDENTIFIER_RE.findall(source):
            tokens.append(word if _is_keyword_common(word) else "<ID>")
        return tokens


def _is_keyword_common(word: str) -> bool:
    """检查是否为常见语言关键字."""
    js_keywords = {
        "var", "let", "const", "function", "return", "if", "else",
        "for", "while", "do", "switch", "case", "break", "continue",
        "new", "this", "class", "extends", "super", "import", "export",
        "default", "from", "try", "catch", "finally", "throw", "async",
        "await", "typeof", "instanceof", "void", "delete", "in", "of",
    }
    return word in js_keywords or word in PYTHON_KEYWORDS


def compute_keyword_vector(tokens: list[str]) -> dict[str, int]:
    """计算关键词频率向量."""
    vector = {}
    for tok in tokens:
        if tok in PYTHON_KEYWORDS or tok in {
            "var", "function", "let", "const", "class", "return",
            "if", "for", "while", "switch", "try", "catch", "import",
        }:
            vector[tok] = vector.get(tok, 0) + 1
    return vector


def fingerprint_file(file_path: str, language: Optional[str] = None) -> CodeFingerprint:
    """对代码文件生成指纹.

    Args:
        file_path: 代码文件路径
        language: 语言类型 ("python" 可进行 AST tokenize), 其他归为通用.

    Returns:
        CodeFingerprint 对象.
    """
    path = Path(file_path)

    if not path.exists():
        return CodeFingerprint(file_path=file_path)

    source = path.read_text(encoding="utf-8", errors="ignore")

    # 检测语言
    if language is None:
        if path.suffix in (".py", ".pyw"):
            language = "python"
        elif path.suffix in (".js", ".jsx", ".ts", ".tsx"):
            language = "javascript"
        else:
            language = "generic"

    tokens = tokenize_generic_code(source, language)
    structure_hash = hashlib.sha256(
        " ".join(tokens).encode()
    ).hexdigest()[:32]
    keyword_vector = compute_keyword_vector(tokens)
    line_count = source.count('\n') + 1

    # 计算注释占比 (Python)
    comment_lines = 0
    if language == "python":
        for line in source.split('\n'):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                comment_lines += 1
        comment_ratio = comment_lines / max(1, line_count)
    else:
        comment_ratio = 0.0

    return CodeFingerprint(
        file_path=file_path,
        normalized_tokens=tokens,
        structure_hash=structure_hash,
        keyword_vector=keyword_vector,
        line_count=line_count,
        comment_ratio=comment_ratio,
    )


def cosine_similarity(vec1: dict[str, int], vec2: dict[str, int]) -> float:
    """计算两个向量的余弦相似度."""
    all_keys = set(vec1.keys()) | set(vec2.keys())
    if not all_keys:
        return 0.0

    dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in all_keys)
    norm1 = sum(v ** 2 for v in vec1.values()) ** 0.5
    norm2 = sum(v ** 2 for v in vec2.values()) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def lcs_length(seq1: list[str], seq2: list[str]) -> int:
    """最长公共子序列长度 (动态规划)."""
    m, n = len(seq1), len(seq2)
    # 对大序列降级处理
    max_seq = 500
    if m > max_seq or n > max_seq:
        # 取前 max_seq 个 token
        seq1 = seq1[:max_seq]
        seq2 = seq2[:max_seq]
        m, n = len(seq1), len(seq2)

    # 滚动数组优化空间
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, prev

    return prev[n]


def compare_code_files(
    file_a: str,
    file_b: str,
    language: Optional[str] = None,
) -> CodeSimilarityResult:
    """比较两个代码文件的相似度.

    Uses:
    - Token LCS ratio (structure similarity)
    - Keyword cosine similarity

    综合评分 = 0.6 * structure + 0.4 * keyword.
    """
    fp_a = fingerprint_file(file_a, language)
    fp_b = fingerprint_file(file_b, language)

    # 结构相似度 (LCS ratio)
    max_len = max(len(fp_a.normalized_tokens), len(fp_b.normalized_tokens))
    if max_len == 0:
        structure_sim = 0.0
    else:
        lcs = lcs_length(fp_a.normalized_tokens, fp_b.normalized_tokens)
        structure_sim = (2.0 * lcs) / (len(fp_a.normalized_tokens) + len(fp_b.normalized_tokens))

    # 关键词相似度
    keyword_sim = cosine_similarity(fp_a.keyword_vector, fp_b.keyword_vector)

    # 综合评分
    similarity = (0.6 * structure_sim + 0.4 * keyword_sim) * 100.0

    return CodeSimilarityResult(
        file_a=file_a,
        file_b=file_b,
        similarity=min(100.0, similarity),
        structure_similarity=structure_sim * 100.0,
        keyword_similarity=keyword_sim * 100.0,
    )


def compare_code_snippets(
    code_a: str,
    code_b: str,
    language: str = "python",
) -> CodeSimilarityResult:
    """比较两个代码片段的相似度."""
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=f".{language}", delete=False
    ) as fa, tempfile.NamedTemporaryFile(
        mode="w", suffix=f".{language}", delete=False
    ) as fb:
        fa.write(code_a)
        fb.write(code_b)
        fa_path = fa.name
        fb_path = fb.name

    try:
        result = compare_code_files(fa_path, fb_path, language)
        return result
    finally:
        Path(fa_path).unlink(missing_ok=True)
        Path(fb_path).unlink(missing_ok=True)
