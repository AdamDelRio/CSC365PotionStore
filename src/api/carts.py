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
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    if sort_col is search_sort_options.customer_name:
        order_by = db.movies.c.title
    elif sort is movie_sort_options.year:
        order_by = db.movies.c.year
    elif sort is movie_sort_options.rating:
        order_by = sqlalchemy.desc(db.movies.c.imdb_rating)
    else:
        assert False

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": potion_sku,
                "customer_name": customer_name,
                "line_item_total": 5,
                "timestamp": sort_col,
            }
        ],
    }


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
