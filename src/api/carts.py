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
        customer_names_col = connection.execute(sqlalchemy.text("SELECT customer FROM cart_ids")).fetchall()

    customer_names = [row[0] for row in customer_names_col]
    if(new_cart.customer not in customer_names):
        with db.engine.begin() as connection:
            cart = connection.execute(sqlalchemy.text(f"INSERT INTO cart_ids (customer) VALUES ('{new_cart.customer}') RETURNING cart_id"))

        cart_id = cart.fetchone()[0]
        return {"cart_id": cart_id}
    else:
        with db.engine.begin() as connection:
            cart_id = connection.execute(sqlalchemy.text(f"SELECT cart_id FROM cart_ids WHERE customer = '{new_cart.customer}'")).first().cart_id
    
        return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    with db.engine.begin() as connection:
            customer = connection.execute(sqlalchemy.text(f"SELECT customer FROM cart_ids WHERE cart_id = '{cart_id}'")).first().customer

    return {"customer": customer}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"INSERT INTO cart_items (cart_id, potion_id, quantity) VALUES ({cart_id}, (SELECT potion_id FROM potion WHERE sku = '{item_sku}'), {cart_item.quantity})"))
    
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    total_cost = 0
    total_bought = 0
    with db.engine.begin() as connection:
        num_potions_bought = connection.execute(sqlalchemy.text(f"SELECT potion_id, quantity FROM cart_items WHERE cart_id = {cart_id}")).fetchall()
    
    for row in num_potions_bought:
        potion_id, quantity = row
        with db.engine.begin() as connection:
            potions = connection.execute(sqlalchemy.text(f"SELECT quantity, cost FROM potion WHERE potion_id = {potion_id}")).first()
        
        num_potions = potions.quantity
        cost_potions = potions.cost
        if num_potions < quantity:
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text(f"DELETE FROM cart_items WHERE cart_id = {cart_id}"))

            return {"total_potions_bought": 0, "total_gold_paid": 0}
        else:
            total_cost += cost_potions * quantity
            total_bought += quantity
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text(f"UPDATE potion SET quantity = quantity - {quantity} WHERE potion_id = {potion_id}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold + {total_cost}"))
                connection.execute(sqlalchemy.text(f"DELETE FROM cart_items WHERE potion_id = {potion_id} AND cart_id = {cart_id}"))
                connection.execute(sqlalchemy.text(f"UPDATE potion SET quantity = quantity - {quantity} WHERE potion_id = {potion_id}"))

    return {"total_potions_bought": total_bought, "total_gold_paid": total_cost}
