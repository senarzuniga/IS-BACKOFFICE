from __future__ import annotations

from typing import Any, Dict, Optional
import streamlit as st


def _ns_key(namespace: str) -> str:
    return f"wb::{namespace}"


def get_ns_state(namespace: str, defaults: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    key = _ns_key(namespace)
    if key not in st.session_state:
        st.session_state[key] = dict(defaults or {})
    else:
        for k, v in (defaults or {}).items():
            st.session_state[key].setdefault(k, v)
    return st.session_state[key]


def set_ns_value(namespace: str, name: str, value: Any) -> None:
    state = get_ns_state(namespace)
    state[name] = value


def append_ns_history(namespace: str, item: Dict[str, Any], history_key: str = "history") -> None:
    state = get_ns_state(namespace)
    if history_key not in state or not isinstance(state[history_key], list):
        state[history_key] = []
    state[history_key].append(item)
