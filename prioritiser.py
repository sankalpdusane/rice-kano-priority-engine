# This file handles the core prioritisation logic: calling the Groq API, parsing LLM responses, and ranking features.

import groq
import os
import json
import time
from dotenv import load_dotenv
from prompts import PRIORITISER_SYSTEM_PROMPT

load_dotenv()

REQUIRED_KEYS = {"feature_name", "kano_category", "priority_rank", "rationale", "risk", "ship_quarter", "rice_score"}
VALID_KANO = {"Must-have", "Performance", "Delight", "Indifferent"}
VALID_QUARTERS = {"Q1", "Q2", "Q3", "Q4"}

REQUIRED_INPUT_FIELDS = {"name", "reach", "impact", "confidence", "effort"}


def validate_result(result):
    """Validates the parsed LLM response. Returns (bool, str)."""
    if not isinstance(result, list):
        return False, "Expected JSON array"

    for i, item in enumerate(result):
        # Check required keys
        missing = REQUIRED_KEYS - set(item.keys())
        if missing:
            return False, f"Item {i} missing keys: {missing}"

        # Check kano_category
        if item.get("kano_category") not in VALID_KANO:
            return False, f"Item {i} has invalid kano_category: '{item.get('kano_category')}'"

        # Check ship_quarter
        if item.get("ship_quarter") not in VALID_QUARTERS:
            return False, f"Item {i} has invalid ship_quarter: '{item.get('ship_quarter')}'"

        # Coerce priority_rank to int if needed
        if not isinstance(item["priority_rank"], int):
            try:
                item["priority_rank"] = int(item["priority_rank"])
            except (ValueError, TypeError):
                return False, f"Item {i} has invalid priority_rank: '{item.get('priority_rank')}'"

    return True, "OK"


def prioritise_features(features: list[dict]) -> list[dict]:
    """
    Calls the Groq API to prioritise a list of product features.

    Args:
        features: list of feature dicts, each with keys: name, reach, impact, confidence, effort,
                  and optionally description, strategic_goal.

    Returns:
        Sorted list of prioritised feature dicts from the LLM.

    Raises:
        ValueError: on bad input or missing API key.
        RuntimeError: if all retry attempts fail.
    """
    # --- Input validation ---
    if not features:
        raise ValueError("Features list cannot be empty.")
    if len(features) > 20:
        raise ValueError(f"Maximum 20 features allowed; received {len(features)}.")
    for idx, f in enumerate(features):
        missing = REQUIRED_INPUT_FIELDS - set(f.keys())
        if missing:
            raise ValueError(f"Feature at index {idx} is missing required fields: {missing}")

    # --- Groq client ---
    api_key = os.getenv("GROQ_API_KEY")
    if api_key is None:
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to your .env file and restart the app."
        )

    client = groq.Groq(api_key=api_key)

    user_message = "Prioritise these product features:\n" + json.dumps(features)

    last_error = None

    for attempt in range(3):
        if attempt > 0:
            time.sleep(2)

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": PRIORITISER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=2500,
            )

            raw = response.choices[0].message.content

            # Strip markdown fences if present
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[-1] if raw.count("```") >= 2 else raw
                raw = raw.lstrip("json").strip()
                if raw.endswith("```"):
                    raw = raw[:-3].strip()

            # Extract JSON array boundaries
            start = raw.index("[")
            end = raw.rindex("]") + 1
            json_str = raw[start:end]

            parsed = json.loads(json_str)

            valid, message = validate_result(parsed)
            if not valid:
                raise ValueError(f"Validation failed: {message}")

            # Sort by priority_rank ascending
            parsed.sort(key=lambda x: x["priority_rank"])
            return parsed

        except groq.RateLimitError:
            last_error = RuntimeError(
                "Rate limit reached on the Groq API. Please wait a moment and try again."
            )
        except groq.AuthenticationError:
            raise ValueError(
                "Invalid GROQ_API_KEY. Check your .env file and ensure the key is correct."
            )
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(
        f"Prioritisation failed after 3 attempts. Last error: {last_error}"
    )
