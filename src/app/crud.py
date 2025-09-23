from datetime import datetime

from sqlalchemy import func, or_, String
from sqlalchemy.orm import Session
import pandas as pd

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
