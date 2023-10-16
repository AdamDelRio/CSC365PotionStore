from fastapi import APIRouter
import sqlalchemy
from src import database as db
router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    with db.engine.begin() as connection:
        potion_info = connection.execute(
            sqlalchemy.text(
                "SELECT potion_id, sku, name, quantity, cost, red_ml, green_ml, blue_ml, dark_ml FROM potion WHERE quantity > 0"
            )
        ).fetchall()

    cat_list = []

    for potion in potion_info:
        cat_list.append({
            "potion_id": potion.potion_id,
            "sku": potion.sku,
            "name": potion.name,
            "quantity": potion.quantity,
            "price": potion.cost,
            "potion_type": [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
        })

    return cat_list
