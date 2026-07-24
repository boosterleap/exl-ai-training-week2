# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Dependency layer first so it caches separately from code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm

# Static grounding data can be baked in at build time -- it needs network
# access to the public dataset but no API key. The live pipeline (agent_loop.py,
# governance.py) needs ANTHROPIC_API_KEY, which is never baked into an image --
# it's supplied at `docker run` time and the entrypoint runs the pipeline then.
COPY data/ ./data/
RUN python data/seed_loans_db.py

COPY tools.py agent_loop.py multiagent.py mcp_loan_server.py guardrails.py \
     memory_cache.py observability.py eval_gate.py governance.py app.py \
     entrypoint.sh ./
RUN chmod +x entrypoint.sh

RUN useradd --create-home appuser
USER appuser

EXPOSE 8501
# python:3.12-slim has no curl; a stdlib urllib check avoids an extra apt layer.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
