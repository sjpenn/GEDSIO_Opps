import asyncio
import httpx

async def search():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:5173/api/v1/entities/search?q=IBM")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(search())
