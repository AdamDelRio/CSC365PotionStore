from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("DELETE FROM gold_ledger"))
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (entry, change, description) VALUES ('reset', 100, 'Resetting gold balance to 100')"))
        connection.execute(sqlalchemy.text("DELETE FROM potion_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM customer_orders_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM purchase_history"))
        connection.execute(sqlalchemy.text("DELETE FROM cart_ids"))
        connection.execute(sqlalchemy.text("DELETE FROM ml_ledger"))
        connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (color, entry, change, description) VALUES ('red', 'reset', 0, 'Removing all red barrels from inventory')"))
        connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (color, entry, change, description) VALUES ('green', 'reset', 0, 'Removing all green barrels from inventory')"))
        connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (color, entry, change, description) VALUES ('dark', 'reset', 0, 'Removing all dark barrels from inventory')"))
        potion_types = connection.execute(sqlalchemy.text("SELECT potion_id FROM potion_types"))
        for potion_id in potion_types:
            potion_id = potion_id[0]
            connection.execute(
                sqlalchemy.text("INSERT INTO potion_ledger (entry, change, potion_id, description) VALUES (:entry, :change, :potion_id, :description)"),
                {'entry': 'reset', 'change': 0, 'potion_id': potion_id, 'description': 'Removing all potions from inventory'}
            )

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    return {
        "shop_name": "Adam's Advantageous Analgesics",
        "shop_owner": "Adam Del Rio",
    }

