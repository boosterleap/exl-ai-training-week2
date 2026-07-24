#!/bin/sh
# Runs the live pipeline once (needs ANTHROPIC_API_KEY, supplied at `docker run`
# time -- never baked into the image) if it hasn't been run yet, then starts
# the review UI. Re-running the container with existing outputs/ skips
# straight to the UI.
set -e

if [ ! -f outputs/draft_replies.json ]; then
    echo "No draft_replies.json found -- running the agent pipeline once..."
    python agent_loop.py
    python governance.py
fi

exec streamlit run app.py --server.address 0.0.0.0 --server.port 8501
