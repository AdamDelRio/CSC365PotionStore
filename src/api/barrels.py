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
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {total_price}"))

    total_red_ml = 0
    total_blue_ml = 0
    total_green_ml = 0
    for item in barrels_delivered:
        if(item.sku == "MINI_RED_BARREL" or item.sku == "SMALL_RED_BARREL" or item.sku == "MEDIUM_RED_BARREL"):
            total_red_ml += item.ml_per_barrel
        elif(item.sku == "MINI_GREEN_BARREL" or item.sku == "SMALL_GREEN_BARREL" or item.sku == "MEDIUM_GREEN_BARREL"):
            total_green_ml += item.ml_per_barrel
        else:
            total_blue_ml += item.ml_per_barrel

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml + {total_red_ml}, num_green_ml = num_green_ml + {total_green_ml}, num_blue_ml = num_blue_ml + {total_blue_ml}"))


    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first().num_red_ml
        blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).first().num_blue_ml
        green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).first().num_green_ml
        gold_quantity = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first().gold
        red_ml_takes = connection.execute(sqlalchemy.text("SELECT SUM(red_ml) FROM potion")).scalar()
        green_ml_takes = connection.execute(sqlalchemy.text("SELECT SUM(green_ml) FROM potion")).scalar()
        blue_ml_takes = connection.execute(sqlalchemy.text("SELECT SUM(blue_ml) FROM potion")).scalar()
    
    tot_red = red_ml // (red_ml_takes / 100)

    tot_blue = blue_ml // (blue_ml_takes / 100)

    tot_green = green_ml // (green_ml_takes / 100)

    bar_list = []

    barrel_catalog = {
    "red": {
        "mini": None,
        "small": None,
        "medium": None
    },
    "green": {
        "mini": None,
        "small": None,
        "medium": None
    },
    "blue": {
        "mini": None,
        "small": None,
        "medium": None
    }
    }
    
    for item in wholesale_catalog:
        if(item.sku == "MINI_RED_BARREL"):
            barrel_catalog["red"]["mini"] = item
        elif(item.sku == "SMALL_RED_BARREL"):
            barrel_catalog["red"]["small"] = item
        elif(item.sku == "MEDIUM_RED_BARREL"):
            barrel_catalog["red"]["medium"] = item
        elif(item.sku == "MINI_GREEN_BARREL"):
            barrel_catalog["green"]["mini"] = item
        elif(item.sku == "SMALL_GREEN_BARREL"):
            barrel_catalog["green"]["small"] = item
        elif(item.sku == "MEDIUM_GREEN_BARREL"):
            barrel_catalog["green"]["medium"] = item
        elif(item.sku == "MINI_BLUE_BARREL"):
            barrel_catalog["blue"]["mini"] = item
        elif(item.sku == "SMALL_BLUE_BARREL"):
            barrel_catalog["blue"]["small"] = item
        else:
            barrel_catalog["blue"]["medium"] = item

    prev_gold_quantity = gold_quantity

    while(gold_quantity >= 0):
        mls = sorted([tot_green, tot_red, tot_blue])
        if(gold_quantity <= 220 or (barrel_catalog["red"]["small"] is None and barrel_catalog["red"]["medium"] is None and barrel_catalog["green"]["small"] is None and barrel_catalog["green"]["medium"] is None and barrel_catalog["blue"]["small"] is None and barrel_catalog["blue"]["medium"] is None)):
            if(mls[0] == tot_green and barrel_catalog["green"]["mini"] is not None and gold_quantity >= 60):
                bar_list.append(
                    {
                "sku": "MINI_GREEN_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= 60
                tot_green += 200
                barrel_catalog["green"]["mini"].quantity -= 1
                if(barrel_catalog["green"]["mini"].quantity == 0):
                    barrel_catalog["green"]["mini"] = None
            elif(mls[0] == tot_red and barrel_catalog["red"]["mini"] is not None and gold_quantity >= 60):
                bar_list.append(
                    {
                "sku": "MINI_RED_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= 60
                tot_red += 200
                barrel_catalog["red"]["mini"].quantity -= 1
                if(barrel_catalog["red"]["mini"].quantity == 0):
                    barrel_catalog["red"]["mini"] = None
            elif(mls[0] == tot_blue and barrel_catalog["blue"]["mini"] is not None and gold_quantity >= 60):
                bar_list.append(
                    {
                "sku": "MINI_BLUE_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= 60
                tot_blue += 200
                barrel_catalog["blue"]["mini"].quantity -= 1
                if(barrel_catalog["blue"]["mini"].quantity == 0):
                    barrel_catalog["blue"]["mini"] = None

        elif(gold_quantity <= 550 or (barrel_catalog["green"]["medium"] is None and barrel_catalog["red"]["medium"] is None and barrel_catalog["blue"]["medium"] is None)):
            if(mls[0] == tot_green and barrel_catalog["green"]["small"] is not None and gold_quantity >= 100):
                bar_list.append(
                    {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= 100
                tot_green += 500
                barrel_catalog["green"]["small"].quantity -= 1
                if(barrel_catalog["green"]["small"].quantity == 0):
                    barrel_catalog["green"]["small"] = None
            elif(mls[0] == tot_red and barrel_catalog["red"]["small"] is not None and gold_quantity >= 100):
                bar_list.append(
                    {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= 100
                tot_red += 500
                barrel_catalog["red"]["small"].quantity -= 1
                if(barrel_catalog["red"]["small"].quantity == 0):
                    barrel_catalog["red"]["small"] = None
            elif(mls[0] == tot_blue and barrel_catalog["blue"]["small"] is not None and gold_quantity >= 120):
                bar_list.append(
                    {
                "sku": "SMALL_BLUE_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= 120
                tot_blue += 500
                barrel_catalog["blue"]["small"].quantity -= 1
                if(barrel_catalog["blue"]["small"].quantity == 0):
                    barrel_catalog["blue"]["small"] = None

        else:
            if(mls[0] == tot_green and barrel_catalog["green"]["medium"] is not None and gold_quantity >= 250):
                bar_list.append(
                    {
                "sku": "MEDIUM_GREEN_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= 250
                tot_green += 2500
                barrel_catalog["green"]["medium"].quantity -= 1
                if(barrel_catalog["green"]["medium"].quantity == 0):
                    barrel_catalog["green"]["medium"] = None
            elif(mls[0] == tot_red and barrel_catalog["red"]["medium"] is not None and gold_quantity >= 250):
                bar_list.append(
                    {
                "sku": "MEDIUM_RED_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= 250
                tot_red += 2500
                barrel_catalog["red"]["medium"].quantity -= 1
                if(barrel_catalog["red"]["medium"].quantity == 0):
                    barrel_catalog["red"]["medium"] = None
            elif(mls[0] == tot_blue and barrel_catalog["blue"]["medium"] is not None and gold_quantity >= 300):
                bar_list.append(
                    {
                "sku": "MEDIUM_BLUE_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= 300
                tot_blue += 2500
                barrel_catalog["blue"]["medium"].quantity -= 1
                if(barrel_catalog["blue"]["medium"].quantity == 0):
                    barrel_catalog["blue"]["medium"] = None

        if gold_quantity == prev_gold_quantity:
            break
        prev_gold_quantity = gold_quantity
    
    return bar_list