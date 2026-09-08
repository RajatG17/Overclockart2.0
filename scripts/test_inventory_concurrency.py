import asyncio 
import httpx

PRODUCT_ID = "97c96e10-7315-4645-9dd8-b576b28f1718"

URL = (
    f"http://localhost:8001"
    f"/catalog/inventory/{PRODUCT_ID}/reserve"
)

async def reserve(
        client: httpx.AsyncClient,
        request_number: int,
) -> None:
    response = await client.post(
        URL, 
        json={"quantity": 10},
    )

    print(
        request_number,
        response.status_code,
        response.json(),
    )

async def main() -> None:
    async with httpx.AsyncClient() as client:
        await asyncio.gather(
            reserve(client, 1),
            reserve(client, 2)
        )

asyncio.run(main())