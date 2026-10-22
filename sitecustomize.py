import asyncio

if not hasattr(asyncio, 'Runner'):
    asyncio.Runner = object
