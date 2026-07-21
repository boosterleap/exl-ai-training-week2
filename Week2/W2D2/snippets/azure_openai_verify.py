"""One bounded Azure OpenAI chat-completions call — setup verification only.

Confirms your standalone Azure OpenAI resource, model deployment, and
credentials are wired correctly end-to-end. Makes exactly ONE chat
completion call and prints the result. This checks the raw model-serving
API only — it is not a Microsoft Agent Framework exercise (see the scope
note in VM-Clouds/_AZURE_SANDBOX_SETUP.html).

Auth: set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and
AZURE_OPENAI_DEPLOYMENT as environment variables before running this — see
VM-Clouds/_AZURE_SANDBOX_SETUP.html for the exact portal/CLI steps. Do not
hardcode the key in this file.

Run it:
    python W2D2/snippets/azure_openai_verify.py
"""

from __future__ import annotations

import os
import sys

from openai import AzureOpenAI

AZURE_OPENAI_API_VERSION = "2024-10-21"

REQUIRED_ENV_VARS = ("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT")


def main() -> None:
    # Windows consoles default to a legacy codepage (e.g. cp1252) that can't
    # encode characters models commonly use (curly quotes, non-breaking hyphens).
    sys.stdout.reconfigure(encoding="utf-8")

    missing = [name for name in REQUIRED_ENV_VARS if name not in os.environ]
    if missing:
        raise RuntimeError(
            f"Missing environment variable(s): {', '.join(missing)}. "
            "Set them first — see VM-Clouds/_AZURE_SANDBOX_SETUP.html Step 4."
        )

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=AZURE_OPENAI_API_VERSION,
    )
    resp = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {
                "role": "user",
                "content": "One sentence: what does the 2025-generation Microsoft agent orchestration SDK do?",
            }
        ],
        max_completion_tokens=600,
    )
    print(resp.choices[0].message.content)


if __name__ == "__main__":
    main()
