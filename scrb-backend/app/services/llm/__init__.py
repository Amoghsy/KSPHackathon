"""
app/services/llm — Google Gemini LLM integration layer.

Provides a reusable, configurable service for all AI-powered features.

Components:
    - base.py           — Abstract BaseLLMProvider + shared data classes
    - gemini_provider.py — Concrete Gemini implementation
    - llm_factory.py     — Factory pattern for provider creation
    - prompt_builder.py  — Template-based prompt composition
    - llm_service.py     — Legacy standalone service (backward-compatible)
"""
