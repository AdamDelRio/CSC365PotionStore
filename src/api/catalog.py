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

    with db.engine.begin() as connection:
        blue_potion_quantity = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).first().num_blue_potions

    with db.engine.begin() as connection:
        green_potion_quantity = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).first().num_green_potions


    # Can return a max of 20 items.
    cat_list = []

    if red_potion_quantity > 0:
        cat_list.append({
            "sku": "RED_POTION_0",
            "name": "red potion",
            "quantity": red_potion_quantity,
            "price": 80,
            "potion_type": [100, 0, 0, 0],
        })

    if blue_potion_quantity > 0:
        cat_list.append({
            "sku": "BLUE_POTION_0",
            "name": "blue potion",
            "quantity": blue_potion_quantity,
            "price": 1,
            "potion_type": [0, 0, 100, 0],
        })

    if green_potion_quantity > 0:
        cat_list.append({
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": green_potion_quantity,
            "price": 80,
            "potion_type": [0, 100, 0, 0],
        })

    return cat_list
