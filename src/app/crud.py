from sqlalchemy.orm import Session
from datetime import datetime

from app import models, schemas


def get_item(db: Session, item_id: int):
    return db.query(models.ItemModel).filter(models.ItemModel.id == item_id).first()


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ItemModel).offset(skip).limit(limit).all()


def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.ItemModel(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_items_by_date(db: Session, start_date: datetime, end_date: datetime, operation_types: list[str] = ["MANUAL_VALIDATION", "AUTOMATIC_VALIDATION"]):
    return (
        db.query(models.ItemModel).filter(
            models.ItemModel.created_at.between(start_date, end_date),
            models.ItemModel.operation_type.in_(operation_types)
        )
        .all()
    )
