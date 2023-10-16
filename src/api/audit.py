from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        result_potions = connection.execute(
            sqlalchemy.text(
                "SELECT SUM(quantity) FROM potion"
            )
        ).first()[0]
        result_ml = connection.execute(
            sqlalchemy.text(
                "SELECT num_red_ml, num_blue_ml, num_green_ml, num_dark_ml, gold FROM global_inventory"
            )
        ).first()
    
    return {"number_of_potions": result_potions, "ml_in_barrels": result_ml.num_red_ml + result_ml.num_green_ml + result_ml.num_blue_ml + result_ml.num_dark_ml, "gold": result_ml.gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"