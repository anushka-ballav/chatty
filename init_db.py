from database import Base, sync_engine
import models   # <--- force load models
from config import settings

print("Connecting to:", settings.DATABASE_URL_SYNC)
print("SQLAlchemy parsed URL:", sync_engine.url)
print("Creating tables...")
Base.metadata.create_all(bind=sync_engine)
print("✅ Tables created successfully.")
