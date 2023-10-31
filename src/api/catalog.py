from fastapi import APIRouter
import sqlalchemy
from src import database as db
router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    with db.engine.begin() as connection:
        potion_info = connection.execute(
            sqlalchemy.text(
                """
                SELECT pt.potion_id, pt.sku, pt.name, pt.cost, pt.red_ml, pt.green_ml,  pt.dark_ml, 
                COALESCE(SUM(pl.change), 0) as quantity
                FROM potion_types pt
                LEFT JOIN potion_ledger pl ON pt.potion_id = pl.potion_id
                GROUP BY pt.potion_id, pt.sku, pt.name, pt.cost, pt.red_ml, pt.green_ml, pt.dark_ml
                HAVING COALESCE(SUM(pl.change), 0) > 0
                """
            )
        ).fetchall()

        cat_list = []

        for potion in potion_info:
            if potion.quantity > 0:
                cat_list.append({
                    "sku": potion.sku,
                    "name": potion.name,
                    "quantity": potion.quantity,
                    "price": potion.cost,
                    "potion_type": [potion.red_ml, potion.green_ml, 0, potion.dark_ml],
                })

    return cat_list
