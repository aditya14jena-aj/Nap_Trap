"""Checks the server without a browser:  python test_client.py [http://localhost:8000]"""
import asyncio
import sys
import aiohttp

URL = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8000').rstrip('/')


async def main():
    async with aiohttp.ClientSession() as s:
        async with s.ws_connect(URL + '/ws', timeout=5) as ws:
            print('connected')
            await ws.send_json({'t': 'create', 'name': 'Test'})
            print('server replied:', await asyncio.wait_for(ws.receive_json(), 5))


asyncio.run(main())