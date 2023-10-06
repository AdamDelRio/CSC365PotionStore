from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)

    with db.engine.begin() as connection:
        num_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first().num_red_ml
    
    used_red_ml = (num_red_ml//100) * 100

    num_red_ml2 = num_red_ml - used_red_ml

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = " + str(num_red_ml2)))

    with db.engine.begin() as connection:
        num_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).first().num_red_potions

    new_red_potions = num_red_ml//100

    num_red_potions = num_red_potions + new_red_potions

    #

    with db.engine.begin() as connection:
        num_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).first().num_blue_ml
    
    used_blue_ml = (num_blue_ml//100) * 100

    num_blue_ml2 = num_blue_ml - used_blue_ml

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = " + str(num_blue_ml2)))

    with db.engine.begin() as connection:
        num_blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).first().num_blue_potions

    new_blue_potions = num_blue_ml//100

    num_blue_potions = num_blue_potions + new_blue_potions

    #

    with db.engine.begin() as connection:
        num_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first().num_green_ml
    
    used_green_ml = (num_green_ml//100) * 100

    num_green_ml2 = num_green_ml - used_green_ml

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = " + str(num_green_ml2)))

    with db.engine.begin() as connection:
        num_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).first().num_green_potions

    new_green_potions = num_green_ml//100

    num_green_potions = num_green_potions + new_green_potions

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_red_potions = " + str(num_red_potions) +
            ", num_green_potions = " + str(num_green_potions) +
            ", num_blue_potions = " + str(num_blue_potions)
        ))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    with db.engine.begin() as connection:
        num_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first().num_red_ml

    with db.engine.begin() as connection:
        num_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first().num_green_ml

    with db.engine.begin() as connection:
        num_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).first().num_blue_ml

    bot_list = [
    {
        "potion_type": [100, 0, 0, 0],
        "quantity": num_red_ml // 100,
    }
    if num_red_ml >= 100 else {},
    {
        "potion_type": [0, 100, 0, 0],
        "quantity": num_green_ml // 100,
    }
    if num_green_ml >= 100 else {},
    {
        "potion_type": [0, 0, 100, 0],
        "quantity": num_blue_ml // 100,
    }
    if num_blue_ml >= 100 else{}
    ]
    
    return bot_list

