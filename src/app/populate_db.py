from datetime import datetime, timedelta

from sqlalchemy import insert
from app import models
from app.database import SessionLocal, engine
from faker import Faker

models.Base.metadata.create_all(bind=engine)

fake = Faker()

items = []
for _ in range(100000):
    date_interval = fake.random_int(min=1, max=30)
    num_caixa_interval = fake.random_int(min=1, max=32)
    hostname = str(fake.random_int(min=1, max=32)).zfill(4)
    operation_type = fake.random_element(elements=("MANUAL_VALIDATION", "AUTOMATIC_VALIDATION"))
    item = {
        "ticket_code": fake.uuid4(),
        "num_ped_ecf": str(fake.random_int()),
        "num_cupom": fake.random_int(),
        "num_caixa": num_caixa_interval if operation_type == "AUTOMATIC_VALIDATION" else None,
        "hostname": hostname,
        "vl_total": fake.random_int(),
        "operation_type": operation_type,
        "success": fake.boolean(chance_of_getting_true=95),
        "message": fake.sentence(),
        "created_at": datetime.now() - timedelta(days=date_interval),
        "updated_at": datetime.now() - timedelta(days=date_interval)
    }
    items.append(item)

chunks = [items[i:i+100] for i in range(0, len(items), 100)]

for chunk in chunks:
    with SessionLocal() as db:
        stmt = insert(models.ItemModel).values(chunk)
        db.execute(stmt)
        db.commit()
