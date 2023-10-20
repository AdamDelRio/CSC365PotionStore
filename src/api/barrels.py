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
        connection.execute(sqlalchemy.text(f"INSERT INTO gold_ledger (entry, change, description) VALUES ('deliver', -{total_price}, 'Delivering barrels')"))

    total_red_ml = 0
    total_blue_ml = 0
    total_green_ml = 0
    total_dark_ml = 0
    for item in barrels_delivered:
        if(item.sku == "MINI_RED_BARREL" or item.sku == "SMALL_RED_BARREL" or item.sku == "MEDIUM_RED_BARREL" or item.sku == "LARGE_RED_BARREL"):
            total_red_ml += item.ml_per_barrel * item.quantity
        elif(item.sku == "MINI_GREEN_BARREL" or item.sku == "SMALL_GREEN_BARREL" or item.sku == "MEDIUM_GREEN_BARREL" or item.sku == "LARGE_GREEN_BARREL"):
            total_green_ml += item.ml_per_barrel * item.quantity
        elif(item.sku == "MINI_BLUE_BARREL" or item.sku == "SMALL_BLUE_BARREL" or item.sku == "MEDIUM_BLUE_BARREL" or item.sku == "LARGE_BLUE_BARREL"):
            total_blue_ml += item.ml_per_barrel * item.quantity
        elif(item.sku == "MINI_DARK_BARREL" or item.sku == "SMALL_DARK_BARREL" or item.sku == "MEDIUM_DARK_BARREL" or item.sku == "LARGE_DARK_BARREL"):
            total_dark_ml += item.ml_per_barrel * item.quantity

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"INSERT INTO ml_ledger (color, entry, change, description) VALUES ('red', 'deliver', {total_red_ml}, 'Delivering red barrels')"))
        connection.execute(sqlalchemy.text(f"INSERT INTO ml_ledger (color, entry, change, description) VALUES ('green', 'deliver', {total_green_ml}, 'Delivering green barrels')"))
        connection.execute(sqlalchemy.text(f"INSERT INTO ml_ledger (color, entry, change, description) VALUES ('blue', 'deliver', {total_blue_ml}, 'Delivering blue barrels')"))
        connection.execute(sqlalchemy.text(f"INSERT INTO ml_ledger (color, entry, change, description) VALUES ('dark', 'deliver', {total_dark_ml}, 'Delivering dark barrels')"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        red_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM ml_ledger WHERE color = 'red'")).first()[0]
        blue_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM ml_ledger WHERE color = 'blue'")).first()[0]
        green_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM ml_ledger WHERE color = 'green'")).first()[0]
        dark_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM ml_ledger WHERE color = 'dark'")).first()[0]
        red_ml_takes = connection.execute(sqlalchemy.text("SELECT SUM(red_ml) FROM potion_types")).scalar()
        green_ml_takes = connection.execute(sqlalchemy.text("SELECT SUM(green_ml) FROM potion_types")).scalar()
        blue_ml_takes = connection.execute(sqlalchemy.text("SELECT SUM(blue_ml) FROM potion_types")).scalar()
        dark_ml_takes = connection.execute(sqlalchemy.text("SELECT SUM(dark_ml) FROM potion_types")).scalar()
        gold_quantity = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM gold_ledger")).scalar()

    tot_red = red_ml // (red_ml_takes / 100)
    tot_blue = blue_ml // (blue_ml_takes / 100)
    tot_green = green_ml // (green_ml_takes / 100)
    tot_dark = dark_ml // (dark_ml_takes / 100)

    bar_list = []

    barrel_catalog = {
    "red": {
        "mini": None,
        "small": None,
        "medium": None,
        "large": None
    },
    "green": {
        "mini": None,
        "small": None,
        "medium": None,
        "large": None
    },
    "blue": {
        "mini": None,
        "small": None,
        "medium": None,
        "large": None
    },
    "dark": {
        "mini": None,
        "small": None,
        "medium": None,
        "large": None
    }
    }
    
    for item in wholesale_catalog:
        if(item.sku == "MINI_RED_BARREL"):
            barrel_catalog["red"]["mini"] = item
        elif(item.sku == "SMALL_RED_BARREL"):
            barrel_catalog["red"]["small"] = item
        elif(item.sku == "MEDIUM_RED_BARREL"):
            barrel_catalog["red"]["medium"] = item
        elif(item.sku == "LARGE_RED_BARREL"):
            barrel_catalog["red"]["large"] = item
        elif(item.sku == "MINI_GREEN_BARREL"):
            barrel_catalog["green"]["mini"] = item
        elif(item.sku == "SMALL_GREEN_BARREL"):
            barrel_catalog["green"]["small"] = item
        elif(item.sku == "MEDIUM_GREEN_BARREL"):
            barrel_catalog["green"]["medium"] = item
        elif(item.sku == "LARGE_GREEN_BARREL"):
            barrel_catalog["green"]["large"] = item
        elif(item.sku == "MINI_BLUE_BARREL"):
            barrel_catalog["blue"]["mini"] = item
        elif(item.sku == "SMALL_BLUE_BARREL"):
            barrel_catalog["blue"]["small"] = item
        elif(item.sku == "MEDIUM_BLUE_BARREL"):
            barrel_catalog["blue"]["medium"] = item
        elif(item.sku == "LARGE_BLUE_BARREL"):
            barrel_catalog["blue"]["large"] = item
        elif(item.sku == "MINI_DARK_BARREL"):
            barrel_catalog["dark"]["mini"] = item
        elif(item.sku == "SMALL_DARK_BARREL"):
            barrel_catalog["dark"]["small"] = item
        elif(item.sku == "MEDIUM_DARK_BARREL"):
            barrel_catalog["dark"]["medium"] = item
        elif(item.sku == "LARGE_DARK_BARREL"):
            barrel_catalog["dark"]["large"] = item

    prev_gold_quantity = gold_quantity

    while(gold_quantity >= 0):
        mls = sorted([tot_dark, tot_blue, tot_red, tot_green])
        if(gold_quantity <= 220 or (barrel_catalog["red"]["small"] is None and barrel_catalog["red"]["medium"] is None and barrel_catalog["red"]["large"] is None and barrel_catalog["green"]["small"] is None and barrel_catalog["green"]["medium"] is None and barrel_catalog["green"]["large"] is None and barrel_catalog["blue"]["small"] is None and barrel_catalog["blue"]["medium"] is None and barrel_catalog["blue"]["large"] is None and barrel_catalog["dark"]["small"] is None and barrel_catalog["dark"]["medium"] is None and barrel_catalog["dark"]["large"] is None)):
            if(mls[0] == tot_green and barrel_catalog["green"]["mini"] is not None and gold_quantity >= barrel_catalog["green"]["mini"].price):
                bar_list.append(
                    {
                "sku": "MINI_GREEN_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["green"]["mini"].price
                tot_green += barrel_catalog["green"]["mini"].ml_per_barrel
                barrel_catalog["green"]["mini"].quantity -= 1
                if(barrel_catalog["green"]["mini"].quantity == 0):
                    barrel_catalog["green"]["mini"] = None
            elif(mls[0] == tot_red and barrel_catalog["red"]["mini"] is not None and gold_quantity >= barrel_catalog["red"]["mini"].price):
                bar_list.append(
                    {
                "sku": "MINI_RED_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["red"]["mini"].price
                tot_red += barrel_catalog["red"]["mini"].ml_per_barrel
                barrel_catalog["red"]["mini"].quantity -= 1
                if(barrel_catalog["red"]["mini"].quantity == 0):
                    barrel_catalog["red"]["mini"] = None
            elif(mls[0] == tot_blue and barrel_catalog["blue"]["mini"] is not None and gold_quantity >= barrel_catalog["blue"]["mini"].price):
                bar_list.append(
                    {
                "sku": "MINI_BLUE_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["blue"]["mini"].price
                tot_blue += barrel_catalog["blue"]["mini"].ml_per_barrel
                barrel_catalog["blue"]["mini"].quantity -= 1
                if(barrel_catalog["blue"]["mini"].quantity == 0):
                    barrel_catalog["blue"]["mini"] = None
            elif(mls[0] == tot_dark and barrel_catalog["dark"]["mini"] is not None and gold_quantity >= barrel_catalog["dark"]["mini"].price):
                bar_list.append(
                    {
                "sku": "MINI_DARK_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["dark"]["mini"].price
                tot_dark += barrel_catalog["dark"]["mini"].ml_per_barrel
                barrel_catalog["dark"]["mini"].quantity -= 1
                if(barrel_catalog["dark"]["mini"].quantity == 0):
                    barrel_catalog["dark"]["mini"] = None

        elif(gold_quantity <= 550 or (barrel_catalog["green"]["medium"] is None and barrel_catalog["green"]["large"] is None and barrel_catalog["red"]["medium"] is None and barrel_catalog["red"]["large"] is None and barrel_catalog["blue"]["medium"] is None and barrel_catalog["blue"]["large"] is None and barrel_catalog["dark"]["medium"] is None and barrel_catalog["dark"]["large"] is None)):
            if(mls[0] == tot_green and barrel_catalog["green"]["small"] is not None and gold_quantity >= barrel_catalog["green"]["small"].price):
                bar_list.append(
                    {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["green"]["small"].price
                tot_green += barrel_catalog["green"]["small"].ml_per_barrel
                barrel_catalog["green"]["small"].quantity -= 1
                if(barrel_catalog["green"]["small"].quantity == 0):
                    barrel_catalog["green"]["small"] = None
            elif(mls[0] == tot_red and barrel_catalog["red"]["small"] is not None and gold_quantity >= barrel_catalog["red"]["small"].price):
                bar_list.append(
                    {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["red"]["small"].price
                tot_red += barrel_catalog["red"]["small"].ml_per_barrel
                barrel_catalog["red"]["small"].quantity -= 1
                if(barrel_catalog["red"]["small"].quantity == 0):
                    barrel_catalog["red"]["small"] = None
            elif(mls[0] == tot_blue and barrel_catalog["blue"]["small"] is not None and gold_quantity >= barrel_catalog["blue"]["small"].price):
                bar_list.append(
                    {
                "sku": "SMALL_BLUE_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["blue"]["small"].price
                tot_blue += barrel_catalog["blue"]["small"].ml_per_barrel
                barrel_catalog["blue"]["small"].quantity -= 1
                if(barrel_catalog["blue"]["small"].quantity == 0):
                    barrel_catalog["blue"]["small"] = None
            elif(mls[0] == tot_dark and barrel_catalog["dark"]["small"] is not None and gold_quantity >= barrel_catalog["dark"]["small"].price):
                bar_list.append(
                    {
                "sku": "SMALL_DARK_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["dark"]["small"].price
                tot_dark += barrel_catalog["dark"]["small"].ml_per_barrel
                barrel_catalog["blue"]["small"].quantity -= 1
                if(barrel_catalog["dark"]["small"].quantity == 0):
                    barrel_catalog["dark"]["small"] = None

        elif(gold_quantity <= 550 or (barrel_catalog["green"]["large"] is None and barrel_catalog["red"]["large"] is None and barrel_catalog["blue"]["large"] is None and barrel_catalog["dark"]["large"] is None)):
            if(mls[0] == tot_green and barrel_catalog["green"]["medium"] is not None and gold_quantity >= barrel_catalog["green"]["medium"].price):
                bar_list.append(
                    {
                "sku": "MEDIUM_GREEN_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["green"]["medium"].price
                tot_green += barrel_catalog["green"]["medium"].ml_per_barrel
                barrel_catalog["green"]["medium"].quantity -= 1
                if(barrel_catalog["green"]["medium"].quantity == 0):
                    barrel_catalog["green"]["medium"] = None
            elif(mls[0] == tot_red and barrel_catalog["red"]["medium"] is not None and gold_quantity >= barrel_catalog["red"]["medium"].price):
                bar_list.append(
                    {
                "sku": "MEDIUM_RED_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["red"]["medium"].price
                tot_red += barrel_catalog["red"]["medium"].ml_per_barrel
                barrel_catalog["red"]["medium"].quantity -= 1
                if(barrel_catalog["red"]["medium"].quantity == 0):
                    barrel_catalog["red"]["medium"] = None
            elif(mls[0] == tot_blue and barrel_catalog["blue"]["medium"] is not None and gold_quantity >= barrel_catalog["blue"]["medium"].price):
                bar_list.append(
                    {
                "sku": "MEDIUM_BLUE_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["blue"]["medium"].price
                tot_blue += barrel_catalog["blue"]["medium"].ml_per_barrel
                barrel_catalog["blue"]["medium"].quantity -= 1
                if(barrel_catalog["blue"]["medium"].quantity == 0):
                    barrel_catalog["blue"]["medium"] = None
            elif(mls[0] == tot_dark and barrel_catalog["dark"]["medium"] is not None and gold_quantity >= barrel_catalog["dark"]["medium"].price):
                bar_list.append(
                    {
                "sku": "MEDIUM_DARK_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["dark"]["medium"].price
                tot_dark += barrel_catalog["dark"]["medium"].ml_per_barrel
                barrel_catalog["dark"]["medium"].quantity -= 1
                if(barrel_catalog["dark"]["medium"].quantity == 0):
                    barrel_catalog["dark"]["medium"] = None

        else:
            if(mls[0] == tot_green and barrel_catalog["green"]["large"] is not None and gold_quantity >= barrel_catalog["green"]["large"].price):
                bar_list.append(
                    {
                "sku": "LARGE_GREEN_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["green"]["large"].price
                tot_green += barrel_catalog["green"]["large"].ml_per_barrel
                barrel_catalog["green"]["large"].quantity -= 1
                if(barrel_catalog["green"]["large"].quantity == 0):
                    barrel_catalog["green"]["large"] = None
            elif(mls[0] == tot_red and barrel_catalog["red"]["large"] is not None and gold_quantity >= barrel_catalog["red"]["large"].price):
                bar_list.append(
                    {
                "sku": "LARGE_RED_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["red"]["large"].price
                tot_red += barrel_catalog["red"]["large"].ml_per_barrel
                barrel_catalog["red"]["large"].quantity -= 1
                if(barrel_catalog["red"]["large"].quantity == 0):
                    barrel_catalog["red"]["large"] = None
            elif(mls[0] == tot_blue and barrel_catalog["blue"]["large"] is not None and gold_quantity >= barrel_catalog["blue"]["large"].price):
                bar_list.append(
                    {
                "sku": "LARGE_BLUE_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["blue"]["large"].price
                tot_blue += barrel_catalog["blue"]["large"].ml_per_barrel
                barrel_catalog["blue"]["large"].quantity -= 1
                if(barrel_catalog["blue"]["large"].quantity == 0):
                    barrel_catalog["blue"]["large"] = None
            elif(mls[0] == tot_dark and barrel_catalog["dark"]["large"] is not None and gold_quantity >= barrel_catalog["dark"]["large"].price):
                bar_list.append(
                    {
                "sku": "LARGE_DARK_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["dark"]["large"].price
                tot_dark += barrel_catalog["dark"]["large"].ml_per_barrel
                barrel_catalog["dark"]["large"].quantity -= 1
                if(barrel_catalog["dark"]["large"].quantity == 0):
                    barrel_catalog["dark"]["large"] = None

        if gold_quantity == prev_gold_quantity:
            break
        prev_gold_quantity = gold_quantity
    
    return bar_list