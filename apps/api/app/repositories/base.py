from typing import Generic, TypeVar, Type, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get_by_id(self, id: uuid.UUID) -> T | None:
        result = await self.session.execute(select(self.model).filter_by(id=id))
        return result.scalars().first()
    
    async def get_all(self, skip: int = 0, limit: int = 20, filters: dict = None) -> Tuple[List[T], int]:
        query = select(self.model)
        if filters:
            query = query.filter_by(**filters)
        
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
    
    async def update(self, id: uuid.UUID, **kwargs) -> T | None:
        instance = await self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(instance, key, value)
            await self.session.commit()
            await self.session.refresh(instance)
        return instance
    
    async def soft_delete(self, id: uuid.UUID) -> bool:
        instance = await self.get_by_id(id)
        if instance and hasattr(instance, "deleted_at"):
            from datetime import datetime, timezone
            instance.deleted_at = datetime.now(timezone.utc)
            await self.session.commit()
            return True
        return False

    async def count(self, filters: dict = None) -> int:
        query = select(func.count()).select_from(self.model)
        if filters:
            query = query.filter_by(**filters)
        return await self.session.scalar(query)
