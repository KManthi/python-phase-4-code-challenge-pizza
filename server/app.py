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


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class RestaurantResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        restaurants_list = [restaurant.to_dict(only=("id", "name", "address")) for restaurant in restaurants]
        return make_response(jsonify(restaurants_list), 200)
    
class RestaurantByID(Resource):
    def get(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()

        if restaurant:
            restaurant_pizzas = []
            for rp in restaurant.restaurant_pizzas:
                pizza_data = rp.pizza.to_dict(only=("id", "name", "ingredients"))
                restaurant_pizza_data = {
                    "id": rp.id,
                    "restaurant_id": rp.restaurant_id,
                    "pizza_id": rp.pizza_id,
                    "price": rp.price,
                    "pizza": pizza_data
                }
                restaurant_pizzas.append(restaurant_pizza_data)

            restaurant_data = restaurant.to_dict(only=("id", "name", "address"))
            restaurant_data["restaurant_pizzas"] = restaurant_pizzas
            return make_response(jsonify(restaurant_data), 200)
        
        else:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        
class DeleteRestaurantByID(Resource):
    def delete(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()

        if restaurant:
            for rp in restaurant.restaurant_pizzas:
               db.session.delete(rp)
            db.session.delete(restaurant)
            db.session.commit()
            return make_response(jsonify({"message": "Restaurant deleted"}), 204)
        
        else:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        
class PizzasResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        pizzas_list = [pizza.to_dict(only=("id", "name", "ingredients")) for pizza in pizzas]
        return make_response(jsonify(pizzas_list), 200)
    
class CreateRestaurantPizza(Resource):
    def post(self):
        data = request.get_json()
        pizza = Pizza.query.filter_by(id=data.get('pizza_id')).first()
        restaurant = Restaurant.query.filter_by(id=data.get('restaurant_id')).first()

        if pizza and restaurant:
            price = data.get('price')
            if price is None or price < 1 or price > 30:
                return make_response(jsonify({"errors": ["validation errors"]}), 400)

            restaurant_pizza = RestaurantPizza(price=price, pizza_id=data.get('pizza_id'), restaurant_id=data.get('restaurant_id'))
            db.session.add(restaurant_pizza)
            db.session.commit()

            restaurant_pizza_data = {
                "id": restaurant_pizza.id,
                "restaurant_id": restaurant_pizza.restaurant_id,
                "pizza_id": restaurant_pizza.pizza_id,
                "price": restaurant_pizza.price,
                "pizza": pizza.to_dict(only=("id", "name", "ingredients")),
                "restaurant": restaurant.to_dict(only=("id", "name", "address"))
            }
            return make_response(jsonify(restaurant_pizza_data), 201)

        else:
            return make_response(jsonify({"errors": ["Pizza or Restaurant not found."]}), 404)

api.add_resource(RestaurantResource, '/restaurants')
api.add_resource(RestaurantByID, '/restaurants/<int:id>')
api.add_resource(DeleteRestaurantByID, '/restaurants/<int:id>', methods=["DELETE"])
api.add_resource(PizzasResource, '/pizzas')
api.add_resource(CreateRestaurantPizza, '/restaurant_pizzas')

if __name__ == "__main__":
    app.run(port=5555, debug=True)
