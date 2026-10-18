# File: backend/app/rpc/rpc_client_demo.py
# Description: Client demonstration script illustrating high-speed batch RPC calls to SwasthyaGrid AI

import time
import httpx
import asyncio

RPC_URL = "http://127.0.0.1:8000/api/rpc/v1"

async def test_rpc_io():
    async with httpx.AsyncClient() as client:
        print("[RPC Client] Sending batch telemetry and AI forecast requests...")
        
        batch_payload = [
            {
                "jsonrpc": "2.0",
                "method": "telemetry.ping",
                "params": {},
                "id": 1
            },
            {
                "jsonrpc": "2.0",
                "method": "ai.getDemandForecast",
                "params": {
                    "facility_id": "demo-phc",
                    "facility_name": "PHC Khed Shivapur",
                    "metric_type": "patient_footfall",
                    "daily_burn_rate": 85.0
                },
                "id": 2
            }
        ]
        
        t0 = time.perf_counter()
        response = await client.post(RPC_URL, json=batch_payload)
        elapsed_total = (time.perf_counter() - t0) * 1000
        
        print(f"[RPC Client] Response Received in {elapsed_total:.2f} ms")
        print(response.json())

if __name__ == "__main__":
    asyncio.run(test_rpc_io())

