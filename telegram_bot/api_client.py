"""
API bilan ishlash uchun yordamchi funksiyalar
"""
import aiohttp
from .config import API_BASE_URL


async def api_post(endpoint: str, data: dict, token: str = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE_URL}{endpoint}", json=data, headers=headers) as resp:
            return await resp.json(), resp.status


async def api_get(endpoint: str, token: str = None, params: dict = None) -> dict:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE_URL}{endpoint}", headers=headers, params=params) as resp:
            return await resp.json(), resp.status


async def api_post_multipart(endpoint: str, data: aiohttp.FormData, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE_URL}{endpoint}", data=data, headers=headers) as resp:
            return await resp.json(), resp.status

