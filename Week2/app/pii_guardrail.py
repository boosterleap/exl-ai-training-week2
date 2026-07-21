"""Day 4 -- Presidio PII guardrail, adapted from W2D4/snippets/pii_guardrail.py.

Applied to inbound email bodies before they're logged or passed further
into the pipeline. Uses en_core_web_sm (not Presidio's much larger default
en_core_web_lg) deliberately -- see the collapsible setup note in the
session guide for why that matters on a live-workshop VM.

Run it:
    uv run python -m app.pii_guardrail
"""

from __future__ import annotations

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

SCORE_THRESHOLD = 0.4


def build_analyzer() -> AnalyzerEngine:
    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
    )
    return AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["en"])


def redact(text: str, analyzer: AnalyzerEngine, anonymizer: AnonymizerEngine) -> tuple[str, list[dict]]:
    results = analyzer.analyze(text=text, language="en", score_threshold=SCORE_THRESHOLD)
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    findings = [{"entity_type": r.entity_type, "score": round(r.score, 2), "text": text[r.start : r.end]} for r in results]
    return anonymized.text, findings


if __name__ == "__main__":
    analyzer = build_analyzer()
    anonymizer = AnonymizerEngine()

    sample = (
        "Please contact Jennifer Garcia at jennifer.garcia@example.com or "
        "555-123-4567 about claim CLM-424063."
    )
    redacted, findings = redact(sample, analyzer, anonymizer)
    print("Original: ", sample)
    print("Redacted: ", redacted)
    print("Findings:")
    for f in findings:
        print(f"  {f['entity_type']:16s} score={f['score']:.2f}  {f['text']!r}")
