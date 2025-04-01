#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

# Home route
@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

# GET /restaurants
@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    # Manually create dictionary for the response, excluding 'restaurant_pizzas'
    return jsonify([{
        'id': restaurant.id,
        'name': restaurant.name,
        'address': restaurant.address
    } for restaurant in restaurants])
    
# GET /restaurants/<int:id>
@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant_by_id(id):
    restaurant = Restaurant.query.get(id)
    
    if restaurant:
        # Manually create dictionary for the response, including related restaurant_pizzas
        return jsonify({
            'id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address,
            'restaurant_pizzas': [{
                'id': rp.id,
                'price': rp.price,
                'pizza': {
                    'id': rp.pizza.id,
                    'name': rp.pizza.name,
                    'ingredients': rp.pizza.ingredients
                },
                'restaurant': {
                    'id': rp.restaurant.id,
                    'name': rp.restaurant.name,
                    'address': rp.restaurant.address
                }
            } for rp in restaurant.restaurant_pizzas]
        })
    else:
        return jsonify({'error': 'Restaurant not found'}), 404


# DELETE /restaurants/<int:id>
@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if restaurant:
        # Cascade delete will take care of associated RestaurantPizzas
        db.session.delete(restaurant)
        db.session.commit()
        return make_response('', 204)  # No content
    else:
        return jsonify({"error": "Restaurant not found"}), 404

# GET /pizzas
@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    # Manually create dictionary for the response, excluding 'restaurant_pizzas'
    return jsonify([{
        'id': pizza.id,
        'name': pizza.name,
        'ingredients': pizza.ingredients
    } for pizza in pizzas])

# POST /restaurant_pizzas
@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()

    price = data.get("price")
    pizza_id = data.get("pizza_id")
    restaurant_id = data.get("restaurant_id")

    # Validate price
    if not (1 <= price <= 30):
        return jsonify({"errors": ["validation errors"]}), 400  # Return a generic validation error message

    # Check if the pizza and restaurant exist
    pizza = Pizza.query.get(pizza_id)
    restaurant = Restaurant.query.get(restaurant_id)

    if not pizza:
        return jsonify({"errors": ["Pizza not found"]}), 404
    if not restaurant:
        return jsonify({"errors": ["Restaurant not found"]}), 404

    try:
        # Create the new RestaurantPizza record
        restaurant_pizza = RestaurantPizza(
            price=price,
            pizza_id=pizza_id,
            restaurant_id=restaurant_id
        )

        db.session.add(restaurant_pizza)
        db.session.commit()

        # Return the newly created RestaurantPizza as a response
        return jsonify({
            "id": restaurant_pizza.id,
            "price": restaurant_pizza.price,
            "pizza_id": restaurant_pizza.pizza_id,
            "restaurant_id": restaurant_pizza.restaurant_id,
            "pizza": {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients
            },
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
            }
        }), 201

    except Exception as e:
        db.session.rollback()  # Rollback the session in case of an error
        return jsonify({"errors": [str(e)]}), 500
