import asyncio
if not hasattr(asyncio, 'Runner'):
    asyncio.Runner = object

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
