from app.models.audit import AuditLog
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import uuid

class AuditService:
    @staticmethod
    def log(db: AsyncSession, user_id: uuid.UUID | None, action: str, resource_type: str, resource_id: str | None = None, ip_address: str | None = None, metadata: dict | None = None):
        async def create_log():
            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                metadata_=metadata
            )
            db.add(log_entry)
            await db.commit()
            
        asyncio.create_task(create_log())
