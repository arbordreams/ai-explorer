
import os
import openai
from ai_scientist.vlm import get_response_from_vlm, create_client

# Set up the dummy environment for the test
# Ensure you have GEMINI_API_KEY in your environment variables
if "GEMINI_API_KEY" not in os.environ:
    print("ERROR: GEMINI_API_KEY not found in environment variables.")
    exit(1)

# Use the actual image from the repo
TEST_IMAGE_PATH = "docs/logo_v1.png"

if not os.path.exists(TEST_IMAGE_PATH):
    print(f"ERROR: Test image {TEST_IMAGE_PATH} not found.")
    exit(1)

MODEL_NAME = "gemini-3-pro-preview"
SYSTEM_MSG = "You are a helpful assistant."
USER_MSG = "Describe this image in detail. What colors and shapes do you see?"

print(f"Testing VLM: {MODEL_NAME}")
print(f"Image: {TEST_IMAGE_PATH}")

try:
    # 1. Create Client
    client, _ = create_client(MODEL_NAME)
    
    # 2. Send Request
    response, history = get_response_from_vlm(
        msg=USER_MSG,
        image_paths=[TEST_IMAGE_PATH],
        client=client,
        model=MODEL_NAME,
        system_message=SYSTEM_MSG,
        print_debug=True
    )

    print("\n✅ SUCCESS: VLM responded!")
    print("-" * 40)
    print(response)
    print("-" * 40)

except Exception as e:
    print("\n❌ FAILURE: VLM check failed.")
    print(e)
    import traceback
    traceback.print_exc()

