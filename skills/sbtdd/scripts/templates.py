#!/usr/bin/env python3
# Author: Julian Bolivar
# Version: 1.0.0
# Date: 2026-04-19
"""Placeholder expansion for template files (sec.S.2.1 templates.py).

expand() substitutes {Key} placeholders using a context dict. Unknown
placeholders are left literal (no KeyError) to enable partial expansion
and forward compatibility with template additions.
"""

from __future__ import annotations

import re
from typing import Mapping

_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def expand(template: str, context: Mapping[str, str]) -> str:
    """Substitute {Key} placeholders in template using context.

    Args:
        template: The template string containing {Key} placeholders.
        context: Mapping of placeholder names → replacement strings.

    Returns:
        The template with known placeholders replaced; unknown
        placeholders are left literal (e.g. "{Unknown}").
    """

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return context.get(key, match.group(0))

    return _PLACEHOLDER_RE.sub(_replace, template)
