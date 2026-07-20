# Agentic library primers

Run these notebooks before the main Week 2 Day 1 sessions:

1. [`01_LANGGRAPH_PRIMER.ipynb`](01_LANGGRAPH_PRIMER.ipynb) before `W2D1AM`
2. [`02_CLAUDE_AGENT_SDK_PRIMER.ipynb`](02_CLAUDE_AGENT_SDK_PRIMER.ipynb) before `W2D1PM`

Select the **Python (EXL Week 2)** kernel (`exl-week2`). On this machine that kernel
uses `C:\Users\Asus\.venv` (not `Week2\.venv`).

The LangGraph primer runs offline with in-code records. The Claude Agent SDK primer
uses small in-code domain records and calls the configured Anthropic / Claude Code
runtime from `Week2/.env`. On Windows Jupyter, live SDK cells use `run_sdk(...)` so
Claude Code can spawn under a Proactor event loop.

These primers introduce the library surfaces. The main AM and PM notebooks and
scripts remain the authoritative Day 1 content.
