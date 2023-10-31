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
    print(potions_delivered)
    used_red_ml = 0
    used_green_ml = 0
    used_dark_ml = 0
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            red_ml = potion.potion_type[0]
            green_ml = potion.potion_type[1]
            dark_ml = potion.potion_type[2]
            

            used_red_ml = red_ml * potion.quantity

            used_green_ml = green_ml * potion.quantity

            used_dark_ml = dark_ml * potion.quantity

            potion_id = connection.execute(
                sqlalchemy.text(
                    "SELECT potion_id FROM potion_types WHERE red_ml = :red_ml AND green_ml = :green_ml AND dark_ml = :dark_ml"
                ),
                {
                    'red_ml': potion.potion_type[0],
                    'green_ml': potion.potion_type[1],
                    'dark_ml': potion.potion_type[2]
                }
            ).first().potion_id

            connection.execute(sqlalchemy.text(
                "INSERT INTO potion_ledger (potion_id, entry, change, description) VALUES (:potion_id, 'bottling', :potion_quantity, 'Bottling operation')"
            ), {"potion_id": potion_id, "potion_quantity": potion.quantity})

            connection.execute(sqlalchemy.text(
                "INSERT INTO ml_ledger (color, entry, change, description) VALUES ('red', 'bottling', :used_red_ml, 'Bottling operation')"
            ), {"used_red_ml": -used_red_ml})

            connection.execute(sqlalchemy.text(
                "INSERT INTO ml_ledger (color, entry, change, description) VALUES ('green', 'bottling', :used_green_ml, 'Bottling operation')"
            ), {"used_green_ml": -used_green_ml})

            connection.execute(sqlalchemy.text(
                "INSERT INTO ml_ledger (color, entry, change, description) VALUES ('dark', 'bottling', :used_dark_ml, 'Bottling operation')"
            ), {"used_dark_ml": -used_dark_ml})

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    with db.engine.begin() as connection:
        potion_info = connection.execute(
            sqlalchemy.text("SELECT potion_id, red_ml, green_ml, dark_ml FROM potion_types")
        ).fetchall()
        potion_ledger_info = connection.execute(
            sqlalchemy.text(
                "SELECT potion_id, SUM(change) FROM potion_ledger GROUP BY potion_id"
            )
        ).fetchall()
        ml_ledger_info = connection.execute(
            sqlalchemy.text(
                "SELECT color, SUM(change) FROM ml_ledger GROUP BY color"
            )
        ).fetchall()
        potion_quantity = connection.execute(
            sqlalchemy.text(
                "SELECT SUM(change) FROM potion_ledger"
            )
        ).scalar()

    potion_dict = {potion_id: change for potion_id, change in potion_ledger_info}
    ml_dict = {color: change for color, change in ml_ledger_info}
    bot_list = []
    count_dict = {potion.potion_id: 0 for potion in potion_info}

    while any(ml >= max(potion.red_ml, potion.green_ml, potion.dark_ml) for ml in ml_dict.values() for potion in potion_info) and potion_quantity <= 294:
        bottle_possible = False

        for potion in sorted(potion_info, key=lambda p: potion_dict.get(p.potion_id, 0)):
            available_red = available_green = available_dark = float("inf")

            if potion.red_ml != 0:
                available_red = ml_dict["red"] // potion.red_ml

            if potion.green_ml != 0:
                available_green = ml_dict["green"] // potion.green_ml

            if potion.dark_ml != 0:
                available_dark = ml_dict["dark"] // potion.dark_ml

            max_available = min(available_red, available_green, available_dark)

            if max_available >= count_dict[potion.potion_id] and count_dict[potion.potion_id] <= 49 and max_available != 0:
                current_potion_type = [potion.red_ml, potion.green_ml, 0, potion.dark_ml]
                if any(x["potion_type"] == current_potion_type for x in bot_list):
                    for x in bot_list:
                        if x["potion_type"] == current_potion_type:
                            x["quantity"] += 1
                            break
                else:
                    bot_list.append(
                        {
                            "potion_type": current_potion_type,
                            "quantity": 1,
                        }
                    )
                bottle_possible = True
                count_dict[potion.potion_id] += 1

                ml_dict["red"] -= potion.red_ml
                ml_dict["green"] -= potion.green_ml
                ml_dict["dark"] -= potion.dark_ml
                potion_quantity += 1

        if not bottle_possible:
            break

    return bot_list
