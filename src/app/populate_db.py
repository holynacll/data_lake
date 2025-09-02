from datetime import datetime, timedelta
from app import models
from app.database import SessionLocal
from faker import Faker


db = SessionLocal()
fake = Faker()

for _ in range(100):
    date_interval = fake.random_int(min=1, max=30)
    item = {
        "ticket_code": fake.uuid4(),
        "num_ped_ecf": fake.random_int(),
        "num_cupom": fake.random_int(),
        "vl_total": fake.random_int(),
        "operation_type": fake.random_element(elements=("MANUAL_VALIDATION", "AUTOMATIC_VALIDATION")),
        "success": fake.boolean(),
        "message": fake.sentence(),
        "created_at": datetime.now() - timedelta(days=date_interval),
        "updated_at": datetime.now() - timedelta(days=date_interval)
    }
    db_item = models.ItemModel(**item)
    db.add(db_item)
db.commit()
db.close()