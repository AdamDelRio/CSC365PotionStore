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
        total_price += item.price * item.quantity
        
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text("INSERT INTO gold_ledger (entry, change, description) VALUES (:entry, :change, :description)"),
            {'entry': 'deliver', 'change': -total_price, 'description': 'Delivering barrels'}
        )


        total_red_ml = 0
        total_green_ml = 0
        total_dark_ml = 0
        for item in barrels_delivered:
            if(item.sku == "MINI_RED_BARREL" or item.sku == "SMALL_RED_BARREL" or item.sku == "MEDIUM_RED_BARREL" or item.sku == "LARGE_RED_BARREL"):
                total_red_ml += item.ml_per_barrel * item.quantity
            elif(item.sku == "MINI_GREEN_BARREL" or item.sku == "SMALL_GREEN_BARREL" or item.sku == "MEDIUM_GREEN_BARREL" or item.sku == "LARGE_GREEN_BARREL"):
                total_green_ml += item.ml_per_barrel * item.quantity
            elif(item.sku == "MINI_DARK_BARREL" or item.sku == "SMALL_DARK_BARREL" or item.sku == "MEDIUM_DARK_BARREL" or item.sku == "LARGE_DARK_BARREL"):
                total_dark_ml += item.ml_per_barrel * item.quantity

        connection.execute(
            sqlalchemy.text("INSERT INTO ml_ledger (color, entry, change, description) VALUES (:color, :entry, :change, :description)"),
            {'color': 'red', 'entry': 'deliver', 'change': total_red_ml, 'description': 'Delivering red barrels'}
        )
        connection.execute(
            sqlalchemy.text("INSERT INTO ml_ledger (color, entry, change, description) VALUES (:color, :entry, :change, :description)"),
            {'color': 'green', 'entry': 'deliver', 'change': total_green_ml, 'description': 'Delivering green barrels'}
        )
        connection.execute(
            sqlalchemy.text("INSERT INTO ml_ledger (color, entry, change, description) VALUES (:color, :entry, :change, :description)"),
            {'color': 'dark', 'entry': 'deliver', 'change': total_dark_ml, 'description': 'Delivering dark barrels'}
        )

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        red_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM ml_ledger WHERE color = 'red'")).first()[0]
        green_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM ml_ledger WHERE color = 'green'")).first()[0]
        dark_ml = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM ml_ledger WHERE color = 'dark'")).first()[0]
        red_ml_takes = connection.execute(sqlalchemy.text("SELECT SUM(red_ml) FROM potion_types")).scalar()
        green_ml_takes = connection.execute(sqlalchemy.text("SELECT SUM(green_ml) FROM potion_types")).scalar()
        dark_ml_takes = connection.execute(sqlalchemy.text("SELECT SUM(dark_ml) FROM potion_types")).scalar()
        gold_quantity = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM gold_ledger")).scalar()
        potion_quantity = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM potion_ledger")).scalar()

    tot_red = red_ml // (red_ml_takes / 100)
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
    "dark": {
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
        elif(item.sku == "LARGE_DARK_BARREL"):
            barrel_catalog["dark"]["large"] = item

    prev_gold_quantity = gold_quantity

    purchase_counts = {"green": 0, "red": 0, "dark": 0}

    if purchase_counts["dark"] < 2 and dark_ml <= 50000:
        while purchase_counts["dark"] < 6 and barrel_catalog["dark"]["large"] is not None and gold_quantity >= barrel_catalog["dark"]["large"].price:
            bar_list.append({
                "sku": "LARGE_DARK_BARREL",
                "quantity": 1
            })
            gold_quantity -= barrel_catalog["dark"]["large"].price
            tot_dark += barrel_catalog["dark"]["large"].ml_per_barrel
            barrel_catalog["dark"]["large"].quantity -= 1
            if barrel_catalog["dark"]["large"].quantity == 0:
                barrel_catalog["dark"]["large"] = None
            purchase_counts["dark"] += 1

    if purchase_counts["red"] < 6 and red_ml <= 50000:
        while purchase_counts["red"] < 6 and barrel_catalog["red"]["large"] is not None and gold_quantity >= barrel_catalog["red"]["large"].price:
            bar_list.append({
                "sku": "LARGE_RED_BARREL",
                "quantity": 1
            })
            gold_quantity -= barrel_catalog["red"]["large"].price
            tot_red += barrel_catalog["red"]["large"].ml_per_barrel
            barrel_catalog["red"]["large"].quantity -= 1
            if barrel_catalog["red"]["large"].quantity == 0:
                barrel_catalog["red"]["large"] = None
            purchase_counts["red"] += 1

    if purchase_counts["green"] < 3 and green_ml <= 50000:
        while purchase_counts["green"] < 6 and barrel_catalog["green"]["large"] is not None and gold_quantity >= barrel_catalog["green"]["large"].price:
            bar_list.append({
                "sku": "LARGE_GREEN_BARREL",
                "quantity": 1
            })
            gold_quantity -= barrel_catalog["green"]["large"].price
            tot_green += barrel_catalog["green"]["large"].ml_per_barrel
            barrel_catalog["green"]["large"].quantity -= 1
            if barrel_catalog["green"]["large"].quantity == 0:
                barrel_catalog["green"]["large"] = None
            purchase_counts["green"] += 1

    while gold_quantity >= 0 and (potion_quantity <= 100 or (red_ml < 5000 or green_ml < 5000)):
        prev_gold_quantity = gold_quantity
        mls = sorted([tot_red, tot_green])
        if(gold_quantity < 120):
            if(mls[0] == tot_red and barrel_catalog["red"]["mini"] not in (None, "null") and gold_quantity >= barrel_catalog["red"]["mini"].price):
                bar_list.append(
                    {
                "sku": "MINI_RED_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["red"]["mini"].price
                red_ml += barrel_catalog["red"]["mini"].ml_per_barrel
                tot_red += barrel_catalog["red"]["mini"].ml_per_barrel
                barrel_catalog["red"]["mini"].quantity -= 1
                if(barrel_catalog["red"]["mini"].quantity == 0):
                    barrel_catalog["red"]["mini"] = None
            elif(mls[0] == tot_green and barrel_catalog["green"]["mini"] not in (None, "null") and gold_quantity >= barrel_catalog["green"]["mini"].price):
                bar_list.append(
                    {
                "sku": "MINI_GREEN_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["green"]["mini"].price
                tot_green += barrel_catalog["green"]["mini"].ml_per_barrel
                green_ml += barrel_catalog["green"]["mini"].ml_per_barrel
                barrel_catalog["green"]["mini"].quantity -= 1
                if(barrel_catalog["green"]["mini"].quantity == 0):
                    barrel_catalog["green"]["mini"] = None

        elif(gold_quantity < 250 or (barrel_catalog["green"]["medium"] in (None, "null") and barrel_catalog["green"]["large"] in (None, "null") and barrel_catalog["red"]["medium"] in (None, "null") and barrel_catalog["red"]["large"] in (None, "null") and barrel_catalog["dark"]["large"] in (None, "null"))):
            if(mls[0] == tot_green and barrel_catalog["green"]["small"] not in (None, "null") and gold_quantity >= barrel_catalog["green"]["small"].price):
                bar_list.append(
                    {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["green"]["small"].price
                tot_green += barrel_catalog["green"]["small"].ml_per_barrel
                green_ml += barrel_catalog["green"]["small"].ml_per_barrel
                barrel_catalog["green"]["small"].quantity -= 1
                if(barrel_catalog["green"]["small"].quantity == 0):
                    barrel_catalog["green"]["small"] = None
            elif(mls[0] == tot_red and barrel_catalog["red"]["small"] not in (None, "null") and gold_quantity >= barrel_catalog["red"]["small"].price):
                bar_list.append(
                    {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["red"]["small"].price
                tot_red += barrel_catalog["red"]["small"].ml_per_barrel
                red_ml += barrel_catalog["red"]["small"].ml_per_barrel
                barrel_catalog["red"]["small"].quantity -= 1
                if(barrel_catalog["red"]["small"].quantity == 0):
                    barrel_catalog["red"]["small"] = None
           
        elif(gold_quantity < 400 or (barrel_catalog["green"]["large"] in (None, "null") and barrel_catalog["red"]["large"] in (None, "null") and barrel_catalog["dark"]["large"] in (None, "null"))):
            if(mls[0] == tot_green and barrel_catalog["green"]["medium"] not in (None, "null") and gold_quantity >= barrel_catalog["green"]["medium"].price):
                bar_list.append(
                    {
                "sku": "MEDIUM_GREEN_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["green"]["medium"].price
                tot_green += barrel_catalog["green"]["medium"].ml_per_barrel
                green_ml += barrel_catalog["green"]["medium"].ml_per_barrel
                barrel_catalog["green"]["medium"].quantity -= 1
                if(barrel_catalog["green"]["medium"].quantity == 0):
                    barrel_catalog["green"]["medium"] = None
            elif(mls[0] == tot_red and barrel_catalog["red"]["medium"] not in (None, "null") and gold_quantity >= barrel_catalog["red"]["medium"].price):
                bar_list.append(
                    {
                "sku": "MEDIUM_RED_BARREL",
                "quantity": 1,
                }
                )
                gold_quantity -= barrel_catalog["red"]["medium"].price
                tot_red += barrel_catalog["red"]["medium"].ml_per_barrel
                red_ml += barrel_catalog["red"]["small"].ml_per_barrel
                barrel_catalog["red"]["medium"].quantity -= 1
                if(barrel_catalog["red"]["medium"].quantity == 0):
                    barrel_catalog["red"]["medium"] = None

        if gold_quantity == prev_gold_quantity:
            break
    
    bar_list0 = []
    return bar_list0