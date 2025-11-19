
import os
import json
import base64
import subprocess
import tempfile
from PIL import Image
import io
import requests
from ai_scientist.llm import create_client, get_response_from_llm
from ai_scientist.vlm import get_response_from_vlm
from ai_scientist.treesearch.backend.backend_openai import query
from ai_scientist.treesearch.backend.utils import FunctionSpec

# Configuration
MODEL_NAME = "gemini-3-pro-preview"
TEST_IMAGE_PATH = "docs/logo_v1.png"

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  TESTING: {title}")
    print("=" * 60)

def print_result(success, message):
    if success:
        print(f"\n✅ SUCCESS: {message}")
    else:
        print(f"\n❌ FAILURE: {message}")

def test_standard_llm_call():
    print_header("Standard LLM Call (Chat Completion)")
    try:
        client, model = create_client(MODEL_NAME)
        system_msg = "You are a helpful AI scientist."
        user_msg = "Explain the concept of 'overfitting' in one sentence."
        
        print(f"Model: {model}")
        print(f"Prompt: {user_msg}")
        
        response, _ = get_response_from_llm(
            prompt=user_msg,
            client=client,
            model=model,
            system_message=system_msg,
            temperature=1.0
        )
        
        print(f"Response: {response}")
        print_result(True, "Standard LLM call completed.")
        return True
    except Exception as e:
        print_result(False, f"Standard LLM call failed: {e}")
        return False

def test_multi_turn_conversation():
    print_header("Multi-turn Conversation (Context History)")
    try:
        client, model = create_client(MODEL_NAME)
        system_msg = "You are a helpful assistant."
        
        # Turn 1
        msg1 = "My favorite color is blue."
        print(f"User: {msg1}")
        response1, history1 = get_response_from_llm(
            prompt=msg1,
            client=client,
            model=model,
            system_message=system_msg,
            temperature=1.0
        )
        print(f"Assistant: {response1}")
        
        # Turn 2 (Ask about the previous turn)
        msg2 = "What is my favorite color?"
        print(f"User: {msg2}")
        response2, history2 = get_response_from_llm(
            prompt=msg2,
            client=client,
            model=model,
            system_message=system_msg,
            msg_history=history1, # Pass history from previous turn
            temperature=1.0
        )
        print(f"Assistant: {response2}")
        
        if "blue" in response2.lower():
            print_result(True, "Context preserved across turns.")
            return True
        else:
            print_result(False, "Context lost. Model did not remember the color.")
            return False
            
    except Exception as e:
        print_result(False, f"Multi-turn test failed: {e}")
        return False

def test_vlm_call():
    print_header("VLM Call (Vision)")
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"Skipping VLM test: Image {TEST_IMAGE_PATH} not found.")
        return False
        
    try:
        client, model = create_client(MODEL_NAME)
        system_msg = "You are a helpful AI scientist."
        user_msg = "What is in this image?"
        
        print(f"Model: {model}")
        print(f"Image: {TEST_IMAGE_PATH}")
        
        response, _ = get_response_from_vlm(
            msg=user_msg,
            image_paths=[TEST_IMAGE_PATH],
            client=client,
            model=model,
            system_message=system_msg,
            temperature=1.0
        )
        
        print(f"Response: {response}")
        print_result(True, "VLM call completed.")
        return True
    except Exception as e:
        print_result(False, f"VLM call failed: {e}")
        return False

def test_structured_output_call():
    print_header("Structured Output (JSON Generation)")
    try:
        client, model = create_client(MODEL_NAME)
        system_msg = "You are a data generator. Output valid JSON only."
        user_msg = """Generate a JSON object describing a machine learning experiment.
        Schema:
        {
            "experiment_name": "string",
            "learning_rate": "float",
            "optimizer": "string"
        }
        """
        
        print(f"Model: {model}")
        print("Requesting JSON output...")
        
        response, _ = get_response_from_llm(
            prompt=user_msg,
            client=client,
            model=model,
            system_message=system_msg,
            temperature=1.0
        )
        
        print(f"Raw Response: {response}")
        
        # Attempt to parse JSON
        try:
            # Strip markdown code blocks if present
            clean_response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_response)
            print(f"Parsed JSON: {json.dumps(data, indent=2)}")
            print_result(True, "Structured output call completed and parsed.")
            return True
        except json.JSONDecodeError:
            print_result(False, "Response was not valid JSON.")
            return False
            
    except Exception as e:
        print_result(False, f"Structured output call failed: {e}")
        return False

def test_function_calling():
    print_header("Function Calling (Tools)")
    try:
        # Define a simple tool
        def calculate_sum(a: int, b: int) -> int:
            """Calculates the sum of two integers."""
            return a + b

        func_spec = FunctionSpec(
            name="calculate_sum",
            json_schema={
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "First number"},
                    "b": {"type": "integer", "description": "Second number"}
                },
                "required": ["a", "b"]
            },
            description="Calculates the sum of two integers."
        )
        
        print(f"Model: {MODEL_NAME}")
        print("Testing tool use: calculate_sum(5, 10)")
        
        # Use the backend query function which handles tool calling logic
        output, _, _, _, _ = query(
            system_message="You are a helpful assistant that can calculate sums.",
            user_message="What is 5 plus 10? Use the calculate_sum tool.",
            func_spec=func_spec,
            model=MODEL_NAME,
            temperature=1.0
        )
        
        print(f"Tool Output: {output}")
        
        if isinstance(output, dict) and "a" in output and "b" in output:
            if output["a"] == 5 and output["b"] == 10:
                print_result(True, "Function calling completed successfully.")
                return True
        
        print_result(False, f"Unexpected tool output: {output}")
        return False
        
    except Exception as e:
        print_result(False, f"Function calling failed: {e}")
        return False

def test_code_generation_and_execution():
    print_header("Code Generation & Execution")
    try:
        client, model = create_client(MODEL_NAME)
        system_msg = "You are a Python coding assistant. Output only valid Python code."
        user_msg = "Write a Python script that prints 'Hello from AI Scientist' and calculates the factorial of 5."
        
        print(f"Model: {model}")
        print("Requesting Python code...")
        
        response, _ = get_response_from_llm(
            prompt=user_msg,
            client=client,
            model=model,
            system_message=system_msg,
            temperature=1.0
        )
        
        # Clean up code block markers
        code = response.replace("```python", "").replace("```", "").strip()
        print(f"Generated Code:\n{code}")
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
            
        print(f"Executing generated code at {tmp_path}...")
        
        # Execute
        result = subprocess.run(['python3', tmp_path], capture_output=True, text=True)
        
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        # Cleanup
        os.unlink(tmp_path)
        
        if result.returncode == 0 and "Hello from AI Scientist" in result.stdout and "120" in result.stdout:
            print_result(True, "Code generation and execution successful.")
            return True
        else:
            print_result(False, "Code execution failed or output incorrect.")
            return False
            
    except Exception as e:
        print_result(False, f"Code gen/exec test failed: {e}")
        return False

def test_semantic_search_tool_generation():
    print_header("Semantic Search Tool Generation & Execution")
    
    s2_api_key = os.environ.get("S2_API_KEY")
    if not s2_api_key:
        print("⚠️ S2_API_KEY not found in environment.")
        print("Skipping real API call verification. Will only verify tool call generation.")
    else:
        print("✅ S2_API_KEY found in environment.")

    try:
        func_spec = FunctionSpec(
            name="search",
            json_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to find relevant papers."}
                },
                "required": ["query"]
            },
            description="Search for research papers using Semantic Scholar."
        )
        
        print(f"Model: {MODEL_NAME}")
        print("Testing search tool generation for query: 'transformer architecture'")
        
        output, _, _, _, _ = query(
            system_message="You are a researcher. Use the search tool to find papers.",
            user_message="Find papers about the transformer architecture.",
            func_spec=func_spec,
            model=MODEL_NAME,
            temperature=1.0
        )
        
        print(f"Tool Output: {output}")
        
        if isinstance(output, dict) and "query" in output:
            if "transformer" in output["query"].lower():
                print("✅ Search tool call generated successfully.")
                
                if s2_api_key:
                    print("Executing real Semantic Scholar search...")
                    # Simple S2 API call
                    url = "https://api.semanticscholar.org/graph/v1/paper/search"
                    params = {
                        "query": output["query"],
                        "limit": 1,
                        "fields": "title,authors,year"
                    }
                    headers = {"x-api-key": s2_api_key}
                    
                    response = requests.get(url, params=params, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"S2 API Response: {json.dumps(data, indent=2)}")
                        if "data" in data and len(data["data"]) > 0:
                            print_result(True, "Real Semantic Scholar search successful.")
                            return True
                        else:
                            print_result(False, "S2 API returned no results.")
                            return False
                    else:
                        print_result(False, f"S2 API failed with status {response.status_code}: {response.text}")
                        return False
                else:
                    print_result(True, "Search tool call generated (API call skipped).")
                    return True
        
        print_result(False, f"Unexpected search tool output: {output}")
        return False
        
    except Exception as e:
        print_result(False, f"Search tool test failed: {e}")
        return False

def test_huggingface_token():
    print_header("Hugging Face Token Verification")
    
    hf_token = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN")
    
    if not hf_token:
        print("⚠️ HUGGINGFACE_API_KEY/HF_TOKEN not found in environment.")
        print("Skipping HF test.")
        return None # None means skipped
    else:
        print("✅ HF Token found in environment.")
    
    print("Verifying access...")
    
    try:
        # Verify token by getting user info
        headers = {"Authorization": f"Bearer {hf_token}"}
        response = requests.get("https://huggingface.co/api/whoami-v2", headers=headers)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"Authenticated as: {user_info.get('name', 'Unknown')}")
            print_result(True, "Hugging Face token is valid.")
            return True
        else:
            print(f"Response: {response.text}")
            print_result(False, f"Hugging Face token invalid. Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"HF verification failed: {e}")
        return False

if __name__ == "__main__":
    if "GEMINI_API_KEY" not in os.environ:
        print("❌ ERROR: GEMINI_API_KEY not found in environment variables.")
        exit(1)

    print(f"Starting Comprehensive Pipeline Test for {MODEL_NAME}...")
    
    results = {
        "LLM (Basic)": test_standard_llm_call(),
        "LLM (Multi-turn)": test_multi_turn_conversation(),
        "VLM (Vision)": test_vlm_call(),
        "JSON Output": test_structured_output_call(),
        "Tool Use (Math)": test_function_calling(),
        "Tool Use (Search)": test_semantic_search_tool_generation(),
        "Code Gen & Exec": test_code_generation_and_execution(),
        "HF Token": test_huggingface_token()
    }
    
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    all_passed = True
    for test, passed in results.items():
        if passed is None:
            status = "⚠️ SKIPPED"
        else:
            status = "✅ PASS" if passed else "❌ FAIL"
            if not passed:
                all_passed = False
        print(f"{test:<25}: {status}")
    
    if all_passed:
        print("\n🎉 All pipeline components verified successfully!")
    else:
        print("\n⚠️ Some components failed. Check logs above.")
