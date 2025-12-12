import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def extract_functions(state: Dict[str, Any]) -> Dict[str, Any]:
    # naive function extractor: split by 'def '
    code = state.get("code", "")
    funcs = []
    for part in code.split("def "):
        if part.strip():
            # take till first '('\
            name = part.split("(")[0].strip()
            funcs.append(name)
    state_update = {"functions": funcs}
    logger.info("Extracted %d functions", len(funcs))
    return state_update


def check_complexity(state: Dict[str, Any]) -> Dict[str, Any]:
    # simple heuristic: complexity = number of lines in each function
    code = state.get("code", "")
    funcs = state.get("functions", [])
    complexities = {f: 1 + code.count('\n') // max(1, len(funcs)) for f in funcs}
    state_update = {"complexities": complexities}
    logger.info("Computed complexities for %d functions", len(complexities))
    return state_update


def detect_issues(state: Dict[str, Any]) -> Dict[str, Any]:
    # detect some simple 'issues' like TODO, FIXME or long lines
    code = state.get("code", "")
    issues = []
    for i, line in enumerate(code.splitlines(), start=1):
        if "TODO" in line or "FIXME" in line:
            issues.append({"line": i, "type": "todo/fixme", "text": line.strip()})
        if len(line) > 120:
            issues.append({"line": i, "type": "long-line", "text": line.strip()})
    state_update = {"issues": issues, "issues_count": len(issues)}
    logger.info("Detected %d issues", len(issues))
    return state_update


def suggest_improvements(state: Dict[str, Any]) -> Dict[str, Any]:
    issues = state.get("issues", [])
    suggestions = []
    for it in issues:
        if it["type"] == "todo/fixme":
            suggestions.append({"line": it["line"], "suggestion": "Resolve or remove TODO/FIXME"})
        elif it["type"] == "long-line":
            suggestions.append({"line": it["line"], "suggestion": "Wrap or shorten the line"})
    # compute a simple quality score
    issues_count = state.get("issues_count", 0)
    quality_score = max(0, 100 - issues_count * 10)
    logger.info("Generated %d suggestions, quality_score=%s", len(suggestions), quality_score)
    return {"suggestions": suggestions, "quality_score": quality_score}
