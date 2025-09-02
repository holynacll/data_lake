from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.database import engine, get_db

models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.APP_NAME,
    description="",
    summary="API REST - Swagger Documentation",
    version=settings.APP_VERSION,
    terms_of_service="https://xtesting.com.br/quem-somos/",
    contact={
        "name": "Alexandre Cury Lima",
        "email": "alexandrecurylima@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/items/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db=db, item=item)


@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


@app.get("/items/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item
