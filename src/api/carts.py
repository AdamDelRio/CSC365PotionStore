from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: str = 'timestamp',
    sort_order: str = 'desc',
):
    with db.engine.begin() as connection:
        query = """
                SELECT
                    cart_ids.customer,
                    potion_types.sku as potion_sku,
                    potion_types.cost,
                    customer_orders_ledger.timestamp,
                    customer_orders_ledger.quantity
                FROM
                    customer_orders_ledger
                INNER JOIN cart_ids ON customer_orders_ledger.cart_id = cart_ids.cart_id
                INNER JOIN potion_types ON customer_orders_ledger.potion_id = potion_types.potion_id
                """

        if customer_name and potion_sku:
            query += """
                     WHERE
                     (cart_ids.customer LIKE :customer_name) 
                     AND (potion_types.sku LIKE :potion_sku)
                     """
        elif customer_name:
            query += """
                     WHERE
                     (cart_ids.customer LIKE :customer_name)
                     """
        elif potion_sku:
            query += """
                     WHERE
                     (potion_types.sku LIKE :potion_sku)
                     """
        
        query += f" ORDER BY {sort_col} {sort_order.upper()} LIMIT 5"

        result = connection.execute(
            sqlalchemy.text(query),
            {
                'customer_name': f"%{customer_name}%" if customer_name else None,
                'potion_sku': f"%{potion_sku}%" if potion_sku else None
            }
        )
        rows = result.fetchall()

    json = {
        "previous": "",
        "next": "",
        "results": [],
    }
    line_item_id = 1
    for row in rows:
        json["results"].append(
            {
                "line_item_id": line_item_id,  # Add a unique line item ID here,
                "item_sku": row.potion_sku,
                "customer_name": row.customer,
                "line_item_total": row.quantity * row.cost,
                "timestamp": row.timestamp,
            }
        )
        line_item_id += 1

    return json

class NewCart(BaseModel):
    customer: str

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        customer_names_col = connection.execute(sqlalchemy.text("SELECT customer FROM cart_ids")).fetchall()

    customer_names = [row[0] for row in customer_names_col]
    if new_cart.customer not in customer_names:
        with db.engine.begin() as connection:
            cart = connection.execute(
                sqlalchemy.text("INSERT INTO cart_ids (customer) VALUES (:customer) RETURNING cart_id"),
                {'customer': new_cart.customer}
            )

        cart_id = cart.fetchone()[0]
        return {"cart_id": cart_id}
    else:
        with db.engine.begin() as connection:
            cart_id = connection.execute(
                sqlalchemy.text("SELECT cart_id FROM cart_ids WHERE customer = :customer"),
                {'customer': new_cart.customer}
            ).first().cart_id

        return {"cart_id": cart_id}



@router.get("/{cart_id}")
def get_cart(cart_id: int):
    with db.engine.begin() as connection:
        customer = connection.execute(
            sqlalchemy.text("SELECT customer FROM cart_ids WHERE cart_id = :cart_id"),
            {'cart_id': cart_id}
        ).first().customer

    return {"customer": customer}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                WITH potion_id_query AS (
                    SELECT potion_id FROM potion_types WHERE sku = :item_sku
                )
                INSERT INTO customer_orders_ledger (cart_id, potion_id, quantity)
                SELECT :cart_id, potion_id, :cart_item_quantity FROM potion_id_query
                """
            ),
            {'item_sku': item_sku, 'cart_id': cart_id, 'cart_item_quantity': cart_item.quantity}
        )

    return "OK"


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    total_cost = 0
    total_bought = 0
    with db.engine.begin() as connection:
        num_potions_bought = connection.execute(
            sqlalchemy.text("SELECT potion_id, quantity FROM customer_orders_ledger WHERE cart_id = :cart_id"),
            {'cart_id': cart_id}
        ).fetchall()

    for row in num_potions_bought:
        potion_id, quantity = row
        with db.engine.begin() as connection:
            potions = connection.execute(
                sqlalchemy.text("SELECT cost, red_ml, green_ml, blue_ml, dark_ml FROM potion_types WHERE potion_id = :potion_id"),
                {'potion_id': potion_id}
            ).first()

        cost_potions = potions.cost
        total_cost += cost_potions * quantity
        total_bought += quantity

        with db.engine.begin() as connection:
            connection.execute(
                sqlalchemy.text("INSERT INTO gold_ledger (entry, change, description) VALUES ('checkout', :total_cost, 'Checkout operation')"),
                {'total_cost': total_cost}
            )
            connection.execute(
                sqlalchemy.text(
                    "INSERT INTO potion_ledger (potion_id, entry, change, description) VALUES (:potion_id, 'checkout', -:quantity, 'Checkout operation')"),
                {'potion_id': potion_id, 'quantity': quantity}
            )

    return {"total_potions_bought": total_bought, "total_gold_paid": total_cost}
