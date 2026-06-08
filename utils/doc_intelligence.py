"""Capa 6: Multi-LLM Consensus Engine con circuit breaker."""
from __future__ import annotations
import asyncio
from typing import Dict, List


class MultiLLMConsensusEngine:
    """Ejecuta N LLMs en paralelo. Si uno falla, circuit breaker lo aísla."""

    def __init__(self) -> None:
        self.providers = {
            "GPT-4":   self._stub("GPT-4"),
            "Claude":  self._stub("Claude"),
            "Gemini":  self._stub("Gemini"),
            "Llama":   self._stub("Llama"),
        }
        self._failures: Dict[str, int] = {}

    def _stub(self, name: str):
        async def _call(content: str, task_type: str) -> Dict:
            await asyncio.sleep(0)  # async no-op
            snippet = (content or "")[:160].replace("\n", " ")
            return {"conclusion": f"[{name}] {task_type}: {snippet}..."}
        return _call

    async def analyze(self, content: str, task_type: str) -> Dict:
        tasks = []
        for name, fn in self.providers.items():
            if self._failures.get(name, 0) >= 3:
                continue  # circuit open
            tasks.append(self._safe_call(name, fn, content, task_type))
        results = await asyncio.gather(*tasks) if tasks else []
        results = {r["name"]: r["result"] for r in results if r}
        return {
            "individual": results,
            "consensus": self._consensus(results),
            "models_used": list(results.keys()),
            "confidence": self._confidence(results),
        }

    async def _safe_call(self, name: str, fn, content: str, task_type: str) -> Dict:
        try:
            r = await fn(content, task_type)
            self._failures[name] = max(0, self._failures.get(name, 0) - 1)
            return {"name": name, "result": r}
        except Exception as e:
            self._failures[name] = self._failures.get(name, 0) + 1
            return {"name": name, "result": {"error": str(e),
                                              "conclusion": f"Error: {e}"}}

    def _consensus(self, results: Dict) -> str:
        valid = [r for r in results.values() if "error" not in r]
        if not valid: return "No se pudo generar consenso."
        return "\n\n".join(f"**{n}**: {r.get('conclusion', '')}" for n, r in valid.items())

    def _confidence(self, results: Dict) -> float:
        valid = [r for r in results.values() if "error" not in r]
        if not valid: return 0.0
        return round(0.5 + 0.1 * len(valid), 3)
