import websockets
import json
import asyncio
async def main():
    try:
        async with websockets.connect('wss://api.deepgram.com/v1/listen',
        # Remember to replace the YOUR_DEEPGRAM_API_KEY placeholder with your Deepgram API Key
        extra_headers = { 'Authorization': f'token YOUR_DEEPGRAM_API_KEY' }) as ws:
            # If the request is successful, print the request ID from the HTTP header
            print('🟢 Successfully opened connection')
            print(f'Request ID: {ws.response_headers["dg-request-id"]}')
            await ws.send(json.dumps({
                'type': 'CloseStream'
            }))
    except websockets.exceptions.InvalidStatusCode as e:
        # If the request fails, print both the error message and the request ID from the HTTP headers
        print(f'🔴 ERROR: Could not connect to Deepgram! {e.headers.get("dg-error")}')
        print(f'🔴 Please contact Deepgram Support with request ID {e.headers.get("dg-request-id")}')
asyncio.run(main())