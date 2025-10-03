"""
Test script to verify backend API format
"""
import asyncio
import aiohttp
import json

async def test_backend():
    backend_url = "http://localhost:50505"
    
    # Test payload similar to what the bot sends
    payload = {
        "messages": [
            {"role": "user", "content": "Care sunt beneficiile?"}
        ],
        "context": {
            "overrides": {
                "temperature": 0.7,
                "top": 3,
                "retrieval_mode": "hybrid",
                "semantic_ranker": True,
                "semantic_captions": True,
            }
        }
    }
    
    print("Testing backend at:", backend_url)
    print("Payload:", json.dumps(payload, indent=2))
    print("\n" + "="*60)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test /chat endpoint
            print("\nTesting /chat endpoint...")
            async with session.post(f"{backend_url}/chat", json=payload) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print("Response keys:", list(data.keys()))
                    if "answer" in data:
                        print("Answer:", data["answer"][:200] + "..." if len(data["answer"]) > 200 else data["answer"])
                    if "citations" in data:
                        print(f"Citations: {len(data['citations'])} found")
                else:
                    text = await response.text()
                    print("Error:", text)
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_backend())
