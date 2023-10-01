from fastapi import APIRouter
import sqlalchemy
from src import database as db
router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        red_potion_quantity = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).first().num_red_potions


    # Can return a max of 20 items.
    if(red_potion_quantity > 0):
        return [
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": red_potion_quantity,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            ]
    else:
        return [
            
        ]
