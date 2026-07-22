# Reference Dockerfile for the W2D0 capstone, Stage 5.
#
# Fallback/reference only -- the session guide asks you to have Claude Code
# build this with you. Not executed/verified during authoring (no Docker
# daemon on the authoring machine) -- the VM's Docker CLI IS confirmed
# installed and running, so build/run this for real there. Standard,
# well-established pattern: slim base, non-root user, model baked in at
# build time (retrain -> rebuild -> redeploy, not a runtime download).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY data_prep.py train_model.py app.py ./
# Bake the trained model into the image at build time, so the container
# never needs live internet access to fetch data or fit a model at runtime.
RUN python data_prep.py && python train_model.py

RUN useradd --create-home appuser
USER appuser

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
