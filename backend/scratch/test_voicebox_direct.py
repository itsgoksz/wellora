import asyncio
import httpx

async def test_voicebox():
    payload = {
        "text": "Hello, I am Wellora, your personal wellness companion. How can I help you?",
        "profile_id": "51f51d17-d8a3-4109-b23e-ac8d7c02f8ff",
        "engine": "kokoro",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        print("Sending generate request to Voicebox...")
        resp = await client.post("http://127.0.0.1:17493/generate", json=payload)
        print("Status:", resp.status_code)
        print("Response JSON:", resp.json())
        
        data = resp.json()
        generation_id = data.get("id")
        if generation_id:
            print(f"Polling history for job: {generation_id}...")
            for i in range(20):
                status_resp = await client.get(f"http://127.0.0.1:17493/history/{generation_id}")
                status_data = status_resp.json()
                print(f"Status response {i}: {status_data}")
                if status_data.get("status") == "completed":
                    print("Job completed!")
                    break
                await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(test_voicebox())
