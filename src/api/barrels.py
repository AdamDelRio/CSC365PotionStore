from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    total_price = 0
    for item in barrels_delivered:
        total_price += item.price
        
    with db.engine.begin() as connection:
        gold_quantity = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first().gold

    gold_quantity = gold_quantity - total_price

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = " + str(gold_quantity)))

    total_ml = 0
    for item in barrels_delivered:
        total_ml += item.ml_per_barrel

    with db.engine.begin() as connection:
        num_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first().num_red_ml

    num_red_ml = num_red_ml + total_ml

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = " + str(num_red_ml)))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).first().num_red_potions

    with db.engine.begin() as connection:
        gold_quantity = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first().gold

    small_red_barrel = None
    for item in wholesale_catalog:
        if item.sku == "SMALL_RED_BARREL":
            small_red_barrel = item
            break
    

    if(red_potions < 10 and small_red_barrel.price <= gold_quantity):
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            }
        ]
    else:
        return [
            
        ]