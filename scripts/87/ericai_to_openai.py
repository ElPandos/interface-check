"""EricAI to OpenAI API Compatibility Layer

This module provides a Flask-based REST API that translates OpenAI-style API calls
to EricAI's API format. It implements a subset of OpenAI's chat completion and
model listing endpoints.

Public Exports:
    app: Flask application instance
    genai_completion: Main completion generation function
    num_tokens_from_messages: Token counting utility
    find_matching_model: Model discovery function

Example Usage:
    # Run the server
    $ python ericai_to_openai.py

    # Make an API call
    $ curl http://localhost:5050/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"messages": [{"role": "user", "content": "Hello"}]}'

Environment Variables:
    ERICAI_API_KEY: API key for EricAI service
    ERICAI_API_BASE: Base URL for EricAI API (optional)
    LOG_LEVEL: Logging level (default: INFO)

Dependencies:
    - Flask
    - EricAI
    - tiktoken
    - python-dotenv
"""

import json
import time
from typing import Any
import uuid

from ericai import EricAI
import tiktoken
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, stream_with_context

app = Flask(__name__)
load_dotenv()


def num_tokens_from_messages(msgs: list[dict[str, str]]) -> int:
    """Count tokens in a list of message dicts using cl100k_base encoding.

    Args:
        msgs: List of message dictionaries with 'content' fields

    Returns:
        Total token count across all message contents
    """
    # Using cl100k_base encoding which is compatible with OpenAI's GPT-4 model
    encoding = tiktoken.get_encoding("cl100k_base")
    return sum(len(encoding.encode(msg["content"])) for msg in msgs)


def find_model(client: EricAI, substring: str, model_type: str = "text-generation") -> Any | None:
    """Find a model matching substring with specified model type.

    Args:
        client: EricAI client instance
        substring: Model ID substring to match
        model_type: Type of model to filter (default: text-generation)

    Returns:
        First matching model object or None if not found
    """
    models = client.models.list()
    # Filter by substring and model type
    matching_models = [
        model
        for model in models.data
        if substring.lower() in model.id.lower() and model.rayllm_metadata["engine_config"]["model_type"] == model_type
    ]
    return matching_models[0] if matching_models else None


def genai_completion(msgs: list[dict[str, str]], model_hint: str = "mistralai/Mistral-Nemo-Instruct-2407") -> Any:
    """Generate completion using EricAI with specific model override.

    Forces usage of Mistral-Nemo-Instruct-2407 regardless of requested model

    Args:
        msgs: List of message dictionaries
        model_hint: Fallback model ID (hardcoded override)

    Returns:
        Completion response object

    Raises:
        ValueError: If target model not found
    """
    client = EricAI()
    # Hardcoded model override for compatibility
    selected_model = find_model(client, model_hint)  # Force model to mistralai/Mistral-Nemo-Instruct-2407
    if not selected_model:
        raise ValueError("Model 'mistralai/Mistral-Nemo-Instruct-2407' not found.")
    print("Selected model:", selected_model.id)
    print("Messages sent to model:", msgs)
    response = client.chat.completions.create(model=selected_model.id, messages=msgs, stream=False)
    print("Response received:", response)
    return response


def extract_text_from_response(response: Any) -> str:
    """Extract content text from completion response.

    Assumes at least one choice exists in response.

    Args:
        response: Completion response object

    Returns:
        Text content from first choice
    """
    return response.choices[0].message.content


@app.route("/v1/chat/completions", methods=["POST"])
def handle_openai() -> Response:
    """Handle OpenAI-compatible chat completion requests.

    Processes both streaming and non-streaming requests.

    Returns:
        Flask Response object with appropriate content type
    """
    data = request.json
    print("Request data:", data)
    stream = data.get("stream", False)
    messages = data.get("messages", [])
    model = data.get("model")
    print("Model Selected from network: ", model)

    if not messages:
        print("Error: No messages provided")
        return jsonify({"error": 'Invalid input. "messages" field is required'}), 400

    try:
        if stream:
            print("Stream is True. Sending streaming response.")

            def generate() -> Response:
                unique_id = str(uuid.uuid4())
                first_chunk = True
                response = genai_completion(messages, model)
                full_response = extract_text_from_response(response)
                print("Full stream response:", full_response)
                # Simulate streaming by chunking response every 50 chars
                for i in range(0, len(full_response), 50):
                    chunk = full_response[i : i + 50]
                    delta = {"content": chunk} if not first_chunk else {"role": "assistant", "content": chunk}
                    first_chunk = False
                    yield f"data: {json.dumps(create_stream_chunk(unique_id, 'mixtral-8x7b', delta))}\n\n"
                # Final chunk with stop signal
                yield f"data: {json.dumps(create_stream_final_chunk(unique_id, 'mixtral-8x7b'))}\n\n"
                yield "data: [DONE]\n\n"

            return Response(stream_with_context(generate()), content_type="text/event-stream")

        else:
            print("Stream is False. Sending single response.")
            response = genai_completion(messages)
            content = extract_text_from_response(response)
            print("Extracted content:", content)
            result = {
                "id": str(uuid.uuid4()),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "mixtral-8x7b",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": num_tokens_from_messages(messages),
                    "completion_tokens": len(content.split()),
                    "total_tokens": num_tokens_from_messages(messages) + len(content.split()),
                },
            }
            print("Final response:", result)
            return jsonify(result)

    except ValueError as ve:
        print("ValueError:", str(ve))
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print("Unexpected error:", str(e))
        return (jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500)


def create_stream_chunk(unique_id: str, model: str, delta: dict) -> dict[str, Any]:
    """Create a streaming response chunk with provided content.

    Args:
        unique_id: UUID for request tracking
        model: Model identifier
        delta: Content delta to include

    Returns:
        Formatted chunk dictionary
    """
    return {
        "id": unique_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
    }


def create_stream_final_chunk(unique_id: str, model: str) -> dict[str, Any]:
    """Create final streaming chunk with stop signal.

    Args:
        unique_id: UUID for request tracking
        model: Model identifier

    Returns:
        Final chunk dictionary
    """
    return {
        "id": unique_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }


@app.route("/v1/models", methods=["GET"])
def handle_models() -> Response:
    """Handle model listing requests.

    Returns list of available models with metadata.

    Returns:
        Flask Response with JSON model list
    """
    client = EricAI()
    models = client.models.list()

    extracted_data = []
    if hasattr(models, "data"):
        for model in models.data:
            running_replicas = model.deployment_status.get("running_replicas", 0)
            if running_replicas > 0:
                extracted_data.append(
                    {
                        "id": model.id,
                        "object": model.object,
                        "created": model.created,
                        "owned_by": model.owned_by,
                        "permission": model.permission,
                        "running_replicas": running_replicas,
                        "max_total_tokens": model.rayllm_metadata["engine_config"].get("max_total_tokens", 0),
                    }
                )
    response_data = {"object": "list", "data": extracted_data}
    return jsonify(response_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
