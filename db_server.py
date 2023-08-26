from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import bcrypt       # hash password
import binascii     # generate token
import os
from datetime import datetime

# import ssl

# API_KEY = "TopSecretAPIKey"


def date_today():
    return datetime.today().strftime('%Y-%m-%d')


app = Flask(__name__)

# -----------------------------------------------------------------------
# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///webshop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = "SECRET_KEY"

# with app.app_context():
#     db.create_all()
# -----------------------------------------------------------------------


class Product(db.Model):
    __tablename__ = 'Product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float(10), nullable=False)
    picture = db.Column(db.String(25), nullable=True)
    id_price_prod = db.Column(db.String(35), nullable=False)
    id_price_test = db.Column(db.String(35), nullable=False)
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# User TABLE Configuration
class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    token = db.Column(db.String(50), nullable=True)
    token_expiration_date = db.Column(db.String(10), nullable=True)
    address = db.Column(db.String(50), nullable=True)
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class ShopOrder(db.Model):
    __tablename__ = 'ShopOrder'  # this stmt is needed, otherwise SQLAlchemy transforms the table name into shop_order
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, nullable=False)
    shipping_address = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(10), nullable=False)
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class OrderLine(db.Model):
    __tablename__ = 'OrderLine'
    id = db.Column(db.Integer, primary_key=True)
    id_order = db.Column(db.Integer, nullable=False)
    seq_nr_order_line = db.Column(db.Integer, nullable=True)
    id_product = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class OrderEvent(db.Model):
    __tablename__ = 'OrderEvent'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    id_order = db.Column(db.Integer, nullable=False)
    id_order_line = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(10), nullable=False)
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# with app.app_context():
#     db.create_all()
# -----------------------------------------------------------------------
# HTTP POST - Create Record - Product
@app.route("/product", methods=["POST"])
def create_product():
    new_product = Product(
        name = request.json["name"],
        description = request.json["description"],
        price = request.json["price"],
        picture = request.json["picture"],
        id_price_prod = request.json["id_price_prod"],
        id_price_test = request.json["id_price_test"]
    )
    try:
        db.session.add(new_product)
        db.session.commit()
    except:
        return jsonify(result={'msg': 'nok, creation failed', 'status': '500'})
    product = new_product.to_dict()
    return jsonify(data={"id": product["id"]},result={'msg': 'ok', 'status': '200'})

# HTTP GET - Read Record - Product
@app.route("/product/<int:id>", methods=["GET"])
def read_product(id):
    try:
        product = db.session.query(Product).filter_by(id=id).first()
        if product:
            return jsonify(data=product.to_dict(), result={'msg': 'ok', 'status': '200'})
        else:
            return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    except:
        return jsonify(result={'msg': 'nok, read failed', 'status': '404'})

# HTTP GET - Read Records - Product
@app.route("/products", methods=["GET"])
def read_product_all():
    try:
        products = db.session.query(Product).all()
        if products:
            return jsonify(products=[product.to_dict() for product in products], result={'msg': 'ok', 'status': '200'})
        else:
            return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    except:
        return jsonify(result={'msg': 'nok, read failed', 'status': '500'})

# HTTP PUT - Update Record - Product
@app.route("/product/<int:id>", methods=["PUT"])
def update_product(id):
    product = db.session.query(Product).filter_by(id=id).first()
    if not product:
        return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    product.name = request.json["name"]
    product.description = request.json["description"]
    product.price = request.json["price"]
    product.picture = request.json["picture"]
    product.id_price_prod = request.json["id_price_prod"]
    product.id_price_test = request.json["id_price_test"]
    try:
        db.session.commit()
        return jsonify(result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, db server error', 'status': '500'})

# HTTP DELETE - Delete Record - Product
@app.route("/product/<int:id>", methods=["DELETE"])
def delete_product(id):
    product = db.session.query(Product).filter_by(id=id).first()
    if not product:
        return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify(result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, db server error', 'status': '500'})


# -----------------------------------------------------------------------
# HTTP POST - Create Record - User
@app.route("/user", methods=["POST"])
def create_user():
    name = request.json["name"]
    email = request.json["email"]
    password = bcrypt.hashpw(request.json["password"].encode('utf8'), bcrypt.gensalt())
    token = binascii.hexlify(os.urandom(20)).decode()
    token_expiration_date = date_today()
    address = request.json["address"]

    print(name, email, password, token, token_expiration_date, address)

    user = db.session.query(User).filter_by(email=email).first()
    if user:
        return jsonify(result={'msg': 'nok, user already exists', 'status': '409'})
    new_user = User(
            name=name,
            email=email,
            password=password,
            token=token,
            token_expiration_date=token_expiration_date,
            address=address
    )
    try:
        db.session.add(new_user)
        db.session.commit()
        db.session.refresh(new_user)  # to get the auto-generated id from the db into our new_user object
    except:
        return jsonify(result={'msg': 'nok, creation failed', 'status': '500'})
    user = new_user.to_dict()
    # user["password"] = ""
    return jsonify(data={"id": user["id"]}, result={'msg': 'ok', 'status': '200'})


# HTTP GET - Read Record - User
@app.route("/user/<int:id>", methods=["GET"])
def read_user(id):
    try:
        user = db.session.query(User).filter_by(id=id).first()
        if not user:
            return jsonify(result={'msg': 'nok, not found', 'status': '404'})
        dic = user.to_dict()
        dic["password"] = ""
        return jsonify(data=dic, result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, read failed', 'status': '500'})


# HTTP GET - Read Record - User
@app.route("/user/check_credentials", methods=["GET"])
def check_credentials():
    email = request.args.get("email")
    password = request.args.get("password")
    user = db.session.query(User).filter_by(email=email).first()
    if not user:
        return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    if bcrypt.checkpw(password.encode('utf8'), user.password):
        user.token = binascii.hexlify(os.urandom(20)).decode()
        user.token_expiration_date = date_today()
        db.session.commit()
        dic = user.to_dict()
        dic["password"] = ""
        return jsonify(data=dic, result={'msg': 'ok', 'status': '200'})
    else:
        return jsonify(result={'msg': 'nok, authentication failed', 'status': '401'})


# HTTP GET - Read Records - User
@app.route("/users", methods=["GET"])
def read_user_all():
    try:
        users = db.session.query(User).all()
        if not users:
            return jsonify(result={'msg': 'nok, not found', 'status': '404'})
        lst = []
        for item in users:
            user = item.to_dict()
            user["password"] = ""
            lst.append(user)
        return jsonify(users=lst, result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, read failed', 'status': '500'})


# HTTP PUT - Update Record - User
@app.route("/user/<int:id>", methods=["PUT"])
def update_user(id):
    user = db.session.query(User).filter_by(id=id).first()
    if not user:
        return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    user.name = request.json["name"]
    user.email = request.json["email"]
    # user.password = bcrypt.hashpw(request.json["password"].encode('utf8'), bcrypt.gensalt())
    # user.token = binascii.hexlify(os.urandom(20)).decode()
    # user.token_expiration_date = date_today()
    user.address = request.json["address"]

    try:
        db.session.commit()
        return jsonify(result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, db server error', 'status': '500'})


# HTTP DELETE - Delete Record - User
@app.route("/user/<int:id>", methods=["DELETE"])
def delete_user(id):
    user = db.session.query(User).filter_by(id=id).first()
    if not user:
        return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify(result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, db server error', 'status': '500'})


# -----------------------------------------------------------------------
# HTTP POST - Create Record - ShopOrder
@app.route("/shop-order", methods=["POST"])
def create_shop_order():
    id_user = request.json["id_user"]
    shipping_address = request.json["shipping_address"]
    status = request.json["status"]
    # validations to be added:
    # id_user exists
    # status in ["initiated", "paid", "completed"]
    new_shop_order = ShopOrder(
        id_user=id_user,
        shipping_address=shipping_address,
        status=status
    )
    try:
        db.session.add(new_shop_order)
        db.session.commit()
        db.session.refresh(new_shop_order)  # to get the auto-generated id from the db into our new object
    except:
        return jsonify(result={'msg': 'nok, creation failed', 'status': '500'})
    shop_order = new_shop_order.to_dict()
    return jsonify(data={'id': shop_order["id"]}, result={'msg': 'ok', 'status': '200'})


# HTTP GET - Read Record - ShopOrder
@app.route("/shop-order/<int:id>", methods=["GET"])
def read_shop_order(id):
    print(id)
    try:
        shop_order = db.session.query(ShopOrder).filter_by(id=id).first()
        if not shop_order:
            return jsonify(result={'msg': 'nok, not found', 'status': '404'})
        return jsonify(data=shop_order.to_dict(), result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, read failed', 'status': '500'})


# HTTP GET - Read Records - ShopOrder
@app.route("/shop-orders", methods=["GET"])
def read_shop_order_all():
    try:
        shop_orders = db.session.query(ShopOrder).all()
        if not shop_orders:
            return jsonify(result={'msg': 'nok, not found', 'status': '404'})
        return jsonify(shop_orders=[shop_order.to_dict() for shop_order in shop_orders], result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, read failed', 'status': '500'})


# HTTP PUT - Update Record - ShopOrder
@app.route("/shop-order/<int:id>", methods=["PUT"])
def update_shop_order(id):
    shop_order = db.session.query(ShopOrder).filter_by(id=id).first()
    if not shop_order:
        return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    shop_order.id_user = request.json["id_user"]
    shop_order.shipping_address = request.json["shipping_address"]
    shop_order.status = request.json["status"]
    # validations to be added:
    # id_user exists
    # status in ["initiated", "paid", "completed"]
    try:
        db.session.commit()
        return jsonify(result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, db server error', 'status': '500'})


# HTTP DELETE - Delete Record - ShopOrder
@app.route("/shop-order/<int:id>", methods=["DELETE"])
def delete_shop_order(id):
    shop_order = db.session.query(ShopOrder).filter_by(id=id).first()
    if not shop_order:
        return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    # cascading delete to be added:
    # delete order_lines, order_events
    try:
        db.session.delete(shop_order)
        db.session.commit()
        return jsonify(result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, db server error', 'status': '500'})


# -----------------------------------------------------------------------
# HTTP POST - Create Record OrderLine
@app.route("/order-line", methods=["POST"])
def create_order_line():
    new_order_line = OrderLine(
        id_order=request.json["id_order"],
        seq_nr_order_line=request.json["seq_nr_order_line"],
        id_product=request.json["id_product"],
        quantity=request.json["quantity"],
        status=request.json["status"]
    )
    # validations to be added:
    # id_order exists
    # id_order_line does not exist
    # id_product exists
    # quantity > 0
    # status in ["initiated", "shipped", "delivered"]
    try:
        db.session.add(new_order_line)
        db.session.commit()
    except:
        return jsonify(result={'msg': 'nok, creation failed', 'status': '500'})
    order_line = new_order_line.to_dict()
    return jsonify(data={"id": order_line["id"]}, result={'msg': 'ok', 'status': '200'})


# HTTP GET - Read Record OrderLine
@app.route("/order-line/<int:id>", methods=["GET"])
def read_order_line(id):
    try:
        order_line = db.session.query(OrderLine).filter_by(id=id).first()
        if not order_line:
            return jsonify(result={'msg': 'nok, not found', 'status': '404'})
        return jsonify(data=order_line.to_dict(), result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, read failed', 'status': '500'})


# HTTP GET - Read Records  OrderLine
@app.route("/order-lines", methods=["GET"])
def read_order_line_all():
    try:
        order_lines = db.session.query(OrderLine).all()
        if not order_lines:
            return jsonify(result={'msg': 'nok, not found', 'status': '404'})
        return jsonify(order_lines=[order_line.to_dict() for order_line in order_lines], result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, read failed', 'status': '500'})


# HTTP PUT - Update Record OrderLine
@app.route("/order-line/<int:id>", methods=["PUT"])
def update_order_line(id):
    order_line = db.session.query(OrderLine).filter_by(id=id).first()
    if not order_line:
        return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    order_line.id_order = request.json["id_order"]
    order_line.seq_nr_order_line = request.json["seq_nr_order_line"]
    order_line.id_product = request.json["id_product"]
    order_line.quantity = request.json["quantity"]
    order_line.status = request.json["status"]
    # validations to be added:
    # id_order exists
    # id_product exists
    # quantity > 0
    # status in ["initiated", "shipped", "delivered"]
    try:
        db.session.commit()
        return jsonify(result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, db server error', 'status': '500'})


# HTTP DELETE - Delete Record OrderLine
@app.route("/order-line/<int:id>", methods=["DELETE"])
def delete_order_line(id):
    order_line = db.session.query(OrderLine).filter_by(id=id).first()
    if not order_line:
        return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    # cascading delete to be added
    # delete order_events
    try:
        db.session.delete(order_line)
        db.session.commit()
        return jsonify(result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, db server error', 'status': '500'})


# -----------------------------------------------------------------------
# HTTP POST - Create Record OrderEvent
@app.route("/order-event", methods=["POST"])
def create_order_event():
    new_order_event = OrderEvent(
        date=request.json["date"],
        id_order=request.json["id_order"],
        id_order_line=request.json["id_order_line"],
        comment=request.json["comment"],
        status=request.json["status"]
    )
    # validations to be added:
    # id_order exists if not empty
    # id_order_line exists if not empty
    # either id_order or id_order_line is not empty
    # status in ["initiated", "paid", "shipped", "delivered", "completed"]
    try:
        db.session.add(new_order_event)
        db.session.commit()
    except:
        return jsonify(result={'msg': 'nok, creation failed', 'status': '500'})
    order_event = new_order_event.to_dict()
    return jsonify(data={"id": order_event["id"]}, result={'msg': 'ok', 'status': '200'})


# HTTP GET - Read Record OrderEvent
@app.route("/order-event/<int:id>", methods=["GET"])
def read_order_event(id):
    try:
        order_event = db.session.query(OrderEvent).filter_by(id=id).first()
        if not order_event:
            return jsonify(result={'msg': 'nok, not found', 'status': '404'})
        return jsonify(data=order_event.to_dict(), result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, read failed', 'status': '500'})


# HTTP GET - Read Records OrderEvent
@app.route("/order-events", methods=["GET"])
def read_order_event_all():
    try:
        order_events = db.session.query(OrderEvent).all()
        if not order_events:
            return jsonify(result={'msg': 'nok, not found', 'status': '404'})
        return jsonify(order_events=[order_event.to_dict() for order_event in order_events], result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, read failed', 'status': '500'})


# HTTP PUT - Update Record OrderEvent
@app.route("/order-event/<int:id>", methods=["PUT"])
def update_order_event(id):
    order_event = db.session.query(OrderEvent).filter_by(id=id).first()
    if not order_event:
        return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    order_event.date = request.json["date"]
    order_event.id_order = request.json["id_order"]
    order_event.id_order_line = request.json["id_order_line"]
    order_event.comment = request.json["comment"]
    order_event.status = request.json["status"]
    # validations to be added:
    # id_order exists if not empty
    # id_order_line exists if not empty
    # either id_order or id_order_line is not empty
    # status in ["initiated", "paid", "shipped", "delivered", "completed"]
    try:
        db.session.commit()
        return jsonify(result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, db server error', 'status': '500'})


# HTTP DELETE - Delete Record OrderEvent
@app.route("/order-event/<int:id>", methods=["DELETE"])
def delete_order_event(id):
    order_event = db.session.query(OrderEvent).filter_by(id=id).first()
    if not order_event:
        return jsonify(result={'msg': 'nok, not found', 'status': '404'})
    try:
        db.session.delete(order_event)
        db.session.commit()
        return jsonify(result={'msg': 'ok', 'status': '200'})
    except:
        return jsonify(result={'msg': 'nok, db server error', 'status': '500'})


# # -----------------------------------------------------------------------
# # HTTP POST - Create Record
# @app.route("/xxx", methods=["POST"])
# def create_xxx():
#     new_xxx = Xxx(
#         a=request.json["a"],
#     )
#     try:
#         db.session.add(new_xxx)
#         db.session.commit()
#     except:
#         return jsonify(result={'msg': 'nok, creation failed', 'status': '500'})
#     xxx = new_xxx.to_dict()
#     return jsonify(data={"id": xxx["id"]}, result={'msg': 'ok', 'status': '200'})
#
#
# # HTTP GET - Read Record
# @app.route("/xxx/<int:id>", methods=["GET"])
# def read_xxx(id):
#     try:
#         xxx = db.session.query(Xxx).filter_by(id=id).first()
#         if not xxx:
#             return jsonify(result={'msg': 'nok, not found', 'status': '404'})
#         return jsonify(data=xxx.to_dict(), result={'msg': 'ok', 'status': '200'})
#     except:
#         return jsonify(result={'msg': 'nok, read failed', 'status': '500'})
#
#
# # HTTP GET - Read Records
# @app.route("/xxxs", methods=["GET"])
# def read_xxx_all():
#     try:
#         xxxs = db.session.query(Xxx).all()
#         if not xxxs:
#             return jsonify(result={'msg': 'nok, not found', 'status': '404'})
#         return jsonify(xxxs=[xxx.to_dict() for xxx in xxxs], result={'msg': 'ok', 'status': '200'})
#     except:
#         return jsonify(result={'msg': 'nok, read failed', 'status': '500'})
#
#
# # HTTP PUT - Update Record
# @app.route("/xxx/<int:id>", methods=["PUT"])
# def update_xxx(id):
#     xxx = db.session.query(Xxx).filter_by(id=id).first()
#     if not xxx:
#         return jsonify(result={'msg': 'nok, not found', 'status': '404'})
#     xxx.a = request.json["a"]
#     try:
#         db.session.commit()
#         return jsonify(result={'msg': 'ok', 'status': '200'})
#     except:
#         return jsonify(result={'msg': 'nok, db server error', 'status': '500'})
#
#
# # HTTP DELETE - Delete Record
# @app.route("/xxx/<int:id>", methods=["DELETE"])
# def delete_xxx(id):
#     xxx = db.session.query(Xxx).filter_by(id=id).first()
#     if not xxx:
#         return jsonify(result={'msg': 'nok, not found', 'status': '404'})
#     try:
#         db.session.delete(xxx)
#         db.session.commit()
#         return jsonify(result={'msg': 'ok', 'status': '200'})
#     except:
#         return jsonify(result={'msg': 'nok, db server error', 'status': '500'})
#
#
# -----------------------------------------------------------------------

if __name__ == "__main__":
    # context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    # context.load_cert_chain('domain.crt', 'domain.key')
    # app.run(port = 5000, debug = True, ssl_context = context)
    app.run(port=5002, debug=True)
