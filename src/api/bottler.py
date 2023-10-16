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
    for potion in potions_delivered:
        with db.engine.begin() as connection:
            potions_bottled = connection.execute(
                sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, dark_ml FROM potion WHERE potion_type = :potion_type"),
                {"potion_type": potion.potion_type}
            ).first()

        red_ml = potions_bottled.red_ml if potions_bottled.red_ml else 0
        green_ml = potions_bottled.green_ml if potions_bottled.green_ml else 0
        blue_ml = potions_bottled.blue_ml if potions_bottled.blue_ml else 0
        dark_ml = potions_bottled.dark_ml if potions_bottled.dark_ml else 0

        used_red_ml = (red_ml // 100) * 100
        remaining_red_ml = red_ml - used_red_ml

        used_green_ml = (green_ml // 100) * 100
        remaining_green_ml = green_ml - used_green_ml

        used_blue_ml = (blue_ml // 100) * 100
        remaining_blue_ml = blue_ml - used_blue_ml

        used_dark_ml = (dark_ml // 100) * 100
        remaining_dark_ml = dark_ml - used_dark_ml

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {remaining_red_ml}, num_green_ml = {remaining_green_ml}, num_blue_ml = {remaining_blue_ml}, num_dark_ml = {remaining_dark_ml}"))
            connection.execute(sqlalchemy.text(f"UPDATE potion SET quantity = quantity + :potion_quantity WHERE potion_type = :potion_type"),
                {"potion_type": potion.potion_type, "potion_quantity": potion.quantity})

    return "OK"


# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():

    with db.engine.begin() as connection:
        potion_info = connection.execute(
            sqlalchemy.text("SELECT potion_id, quantity, red_ml, green_ml, blue_ml, dark_ml FROM potion")
        ).fetchall()

    with db.engine.begin() as connection:
        global_inventory_info = connection.execute(
            sqlalchemy.text(
                "SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory"
            )
        ).first()

    bot_list = []
    available_ml = {
        "red": global_inventory_info.num_red_ml,
        "green": global_inventory_info.num_green_ml,
        "blue": global_inventory_info.num_blue_ml,
        "dark": global_inventory_info.num_dark_ml,
    }
    count_dict = {potion.potion_id: 0 for potion in potion_info}

    while True:
        bottle_possible = False

        for potion in sorted(potion_info, key=lambda p: p.quantity):
            available_red = available_green = available_blue = available_dark = float("inf")

            if potion.red_ml != 0:
                available_red = available_ml["red"] // potion.red_ml

            if potion.green_ml != 0:
                available_green = available_ml["green"] // potion.green_ml

            if potion.blue_ml != 0:
                available_blue = available_ml["blue"] // potion.blue_ml

            if potion.dark_ml != 0:
                available_dark = available_ml["dark"] // potion.dark_ml

            max_available = min(available_red, available_green, available_blue, available_dark)

            if max_available > count_dict[potion.potion_id]:
                current_potion_type = [potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml]
                bot_list = [entry for entry in bot_list if entry['potion_type'] != current_potion_type]
                bot_list.append(
                    {
                        "potion_type": current_potion_type,
                        "quantity": count_dict[potion.potion_id] + 1,
                    }
                )
                count_dict[potion.potion_id] += 1
                bottle_possible = True

                available_ml["red"] -= potion.red_ml
                available_ml["green"] -= potion.green_ml
                available_ml["blue"] -= potion.blue_ml
                available_ml["dark"] -= potion.dark_ml

        if not bottle_possible:
            break

    return bot_list
