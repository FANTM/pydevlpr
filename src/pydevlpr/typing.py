from __future__ import annotations

from typing import Callable, List


__all__ = [
    "Callback",
    "CallbackList"    
]

Callback = Callable[[str], None]
Callback.__doc__ = """Template for function expected by add_callback/remove_callback"""

CallbackList = List[Callback]
CallbackList.__doc__ = """List of functions that are called on new data"""

