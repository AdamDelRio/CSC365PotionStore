from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        customer_names_col = connection.execute(sqlalchemy.text("SELECT customer FROM cart_ids"))

    if(customer_names[0] is None):
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"INSERT INTO cart_ids (cart_id, customer) VALUES (1, '{new_cart.customer}')"))
        return {"cart_id": 1}
    else:
        customer_names = [row[0] for row in customer_names_col]

        if(new_cart.customer not in customer_names):
            with db.engine.begin() as connection:
                cart_id = connection.execute(sqlalchemy.text("SELECT MAX(cart_id) FROM cart_ids")).first().cart_id
                connection.execute(sqlalchemy.text(f"INSERT INTO cart_ids (cart_id, customer) VALUES ({cart_id + 1}, '{new_cart.customer}')"))
                
            return {"cart_id": cart_id + 1}
        else:
            with db.engine.begin() as connection:
                cart_id = connection.execute(sqlalchemy.text(f"SELECT cart_id FROM cart_ids WHERE customer = '{new_cart.customer}'")).first().cart_id
        
            return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return {}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    if(item_sku == "RED_POTION_0"):
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"UPDATE cart_ids SET num_red_potions = '{cart_item.quantity}' WHERE cart_id = {cart_id}"))

    elif(item_sku == "BLUE_POTION_0"):
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"UPDATE cart_ids SET num_blue_potions = '{cart_item.quantity}' WHERE cart_id = {cart_id}"))

    elif(item_sku == "GREEN_POTION_0"):
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"UPDATE cart_ids SET num_green_potions = '{cart_item.quantity}' WHERE cart_id = {cart_id}"))
    
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as connection:
        gold_quantity = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first().gold
        num_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).first().num_red_potions
        num_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).first().num_green_potions
        num_blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).first().num_blue_potions
        sell_red_potions = connection.execute(sqlalchemy.text(f"SELECT num_red_potions FROM cart_ids WHERE cart_id = {cart_id}")).first().num_red_potions
        sell_blue_potions = connection.execute(sqlalchemy.text(f"SELECT num_blue_potions FROM cart_ids WHERE cart_id = {cart_id}")).first().num_blue_potions
        sell_green_potions = connection.execute(sqlalchemy.text(f"SELECT num_green_potions FROM cart_ids WHERE cart_id = {cart_id}")).first().num_green_potions



    
    if(num_red_potions >= sell_red_potions and num_blue_potions >= sell_blue_potions and num_green_potions >= sell_green_potions):
        total_cost = sell_red_potions * 80 + sell_green_potions * 80 + sell_blue_potions * 90
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
            "UPDATE global_inventory SET num_red_potions = " + str(num_red_potions - sell_red_potions) +
            ", num_green_potions = " + str(num_green_potions - sell_green_potions) +
            ", num_blue_potions = " + str(num_blue_potions - sell_blue_potions) +
            ", gold = " + str(gold_quantity + total_cost)
            ))
            connection.execute(sqlalchemy.text(
            "UPDATE cart_ids SET num_red_potions = 0, num_green_potions = 0, num_blue_potions = 0"
            ))
        return {"total_potions_bought": sell_blue_potions + sell_green_potions + sell_red_potions, "total_gold_paid": total_cost}

    else:
        return {"total_potions_bought": 0, "total_gold_paid": 0}
