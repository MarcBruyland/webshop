from flask import Flask, jsonify, render_template, request, redirect, url_for, send_from_directory
from forms import LoginForm, SignupForm, ProductForm, ShippingForm
from flask_bootstrap import Bootstrap
import os
from datetime import datetime
# import datetime
import smtplib
import stripe
import uuid
import requests
import json

# environment variables-----------------------------------------------------------------------
from dotenv.main import load_dotenv
load_dotenv()
run_mode = "test"
# run_mode = "prod"
if run_mode == "test":
    API_KEY = os.environ['API_KEY_TEST']
else:
    API_KEY = os.environ['API_KEY_PROD']
stripe.api_key = API_KEY

SHOP_EMAIL = os.environ['SHOP_EMAIL']
SHOP_EMAIL_PASSWORD = os.environ['SHOP_EMAIL_PASSWORD']

# -----------------------------------------------------------------------

app = Flask(__name__)
bootstrap = Bootstrap(app)

# -----------------------------------------------------------------------
app.secret_key = "SECRET_KEY"

DB_PATH = "http://127.0.0.1:5002"
# -----------------------------------------------------------------------

shopping_cart = {}
store = {'catalog': []}


def date_today():
    return datetime.today().strftime('%Y-%m-%d')


def calculate_total(order):
    result = 0
    for line in order:
        result += line['subtotal']
    return round(result, 2)


def update_shopping_cart(session, product, quantity):
    if session not in shopping_cart:
        shopping_cart[session] = []
    if quantity != 0:
        updated = False
        for line in shopping_cart[session]:
            if line['id_product'] == product["id"]:
                line['quantity'] += quantity
                line['subtotal'] = round(line['quantity'] * product["price"], 2)
                updated = True
        if not updated:
            line_id = len(shopping_cart[session]) + 1
            line = {'id': line_id, 'id_product': product["id"], 'name': product["name"], 'price': product["price"], 'quantity': quantity, 'subtotal': round(quantity * product["price"], 2)}
            shopping_cart[session].append(line)
    return calculate_total(shopping_cart[session])


def send_invoice(session, email):
    with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
        connection.starttls()
        connection.login(user=SHOP_EMAIL, password=SHOP_EMAIL_PASSWORD)
        msg = "Subject:Your order\n\n"
        for line in shopping_cart[session]:
            line_id = line['id']
            id_product = line['id_product']
            quantity = line['quantity']
            subtotal = line['subtotal']
            response = requests.get(DB_PATH + f"/product/{id_product}", params={})
            product = response.json()["data"]
            msg += f"{line_id}: product={id_product} - {product['name']}, quantity={quantity}, subtotal:{subtotal} \n"
        msg += f"total: {calculate_total(shopping_cart[session])}\n"
        msg += f"Your order is fully paid and is being shipped right now !"
        connection.sendmail(
            from_addr=SHOP_EMAIL,
            to_addrs=email,
            msg=msg
        )



def create_event(type, id, status):
    id_order = ""
    id_order_line = ""
    if type == "order":
        id_order = id
    if type == "order_line":
        id_order_line = id

    params = {
        "date": date_today(),
        "id_order": id_order,
        "id_order_line": id_order_line,
        "comment": "",
        "status": status
    }
    response = requests.post(DB_PATH + "/order-event", json=params)
    if response.json()["result"]["msg"] != "ok":
        print(f"ISSUE in create_event: type={type}, id={id}")


# -----------------------------------------------------------------------

@app.route("/")
def home():
    session = str(uuid.uuid4())
    return redirect(f"/products?session={session}")



@app.route("/products", methods=["GET"])
def get_products():
    session = request.args.get('session')
    if not store['catalog']:
        response = requests.get(DB_PATH + "/products", params={})
        store['catalog'] = response.json()['products']
    return render_template("shop.html", catalog=store['catalog'], session=session)


@app.route("/product/<int:id_product>", methods=["GET", "POST"])
def handle_product(id_product):
    session = request.args.get('session')
    form = ProductForm()
    response = requests.get(DB_PATH + f"/product/{id_product}", params={})
    product = response.json()["data"]
    print(product)
    #product = db.session.query(Product).filter_by(id=id_product).first()
    if request.method == "POST":
        quantity = form.quantity.data
        total = update_shopping_cart(session, product, quantity)
        return render_template("shop.html", catalog=store['catalog'], session=session)
    elif request.method == "GET":
        form = ProductForm(
            id=product["id"],
            name=product["name"],
            description=product["description"],
            price=product["price"],
            quantity=0,
            picture=product["picture"]
        )
        return render_template("product.html", form=form, product=product, session=session)


@app.route("/shopping_cart", methods=["GET", "POST"])
def show_cart():
    session = request.args.get('session')
    if session not in shopping_cart:
        shopping_cart[session] = []
    total = calculate_total(shopping_cart[session])
    return render_template("shoppingcart.html", order=shopping_cart[session], session=session, total=total)


@app.route("/increase_quantity")
def increase_quantity():
    session = request.args.get('session')
    id_product = int(request.args.get('id_product'))
    if session not in shopping_cart:
        shopping_cart[session] = []
    for item in shopping_cart[session]:
        if item['id_product'] == id_product:
            item['quantity'] += 1
            item['subtotal'] = round(item['quantity'] * item['price'], 2)
    total = calculate_total(shopping_cart[session])
    return render_template("shoppingcart.html", order=shopping_cart[session], session=session, total=total)


@app.route("/decrease_quantity")
def decrease_quantity():
    session = request.args.get('session')
    id_product = int(request.args.get('id_product'))
    if session not in shopping_cart:
        shopping_cart[session] = []
    ix = 0
    for item in shopping_cart[session]:
        if item['id_product'] == id_product:
            if item['quantity'] > 1:
                item['quantity'] -= 1
                item['subtotal'] = round(item['quantity'] * item['price'], 2)
            else:
                shopping_cart[session].pop(ix)
        ix += 1
    total = calculate_total(shopping_cart[session])
    return render_template("shoppingcart.html", order=shopping_cart[session], session=session, total=total)

# ---------------------------------------------------------------------
# Check out part: 1.signup/login - 2.shipping - 3.payment

@app.route("/signup", methods=["POST", "GET"])
def signup():
    session = request.args.get('session')
    error_msg = ""
    form = SignupForm()
    if form.validate_on_submit():
        params = {
            'name': form.name.data,
            'email': form.email.data,
            'password': form.password.data,
            'address': form.address.data
        }
        print(params)
        response = requests.post(DB_PATH + "/user", json=params)
        print(response.json())
        if response.json()['result']['msg'] == 'ok':
            form = LoginForm()
            return render_template("login.html", form=form, session=session)
        else:
            form = SignupForm()
            error_msg = "User already exists"
    return render_template("signup.html", form=form, msg=error_msg, session=session)


@app.route("/login", methods=["POST", "GET"])
def login():
    session = request.args.get('session')
    error_msg = ""
    form = LoginForm()
    email = form.email.data
    password = form.password.data
    if form.validate_on_submit():
        params = {
            "email": email,
            "password": password
        }
        response = requests.get(DB_PATH + f"/user/check_credentials?email={email}&password={password}")
        if response.json()['result']['msg'] == "ok":
            user = response.json()['data']
            print(user)
            params = {
                "id_user": user["id"],
                "shipping_address": "",
                "status": "initiated"
            }
            response = requests.post(DB_PATH + "/shop-order", json=params)
            if response.json()['result']['msg'] == "ok":
                id_order = response.json()["data"]["id"]
                create_event("order", id_order, "initiated")

                seq_nr_order_line = 1
                for line in shopping_cart[session]:
                    params = {
                        "id_order": id_order,
                        "seq_nr_order_line": seq_nr_order_line,
                        "id_product": line["id_product"],
                        "quantity": line["quantity"],
                        "status": "initiated"
                    }
                    response = requests.post(DB_PATH + "/order-line", json=params)
                    if response.json()['result']['msg'] == "ok":
                        id_order_line = response.json()["data"]["id"]
                        create_event("order_line", id_order_line, "initiated")
                    seq_nr_order_line += 1
                form = ShippingForm(
                    shipping_address=user["address"]
                )
                return render_template("shipping.html", form=form, id_user=user["id"], email=email, session=session, id_order=id_order)
            else:
                error_msg = "db issue, back to shopping cart"
                return render_template("error.html", msg=error_msg)
        else:
            error_msg = "invalid user credentials"
            return render_template("error.html", msg=error_msg)
    else:
        return render_template("login.html", form=form, session=session)


@app.route("/shipping", methods=["POST"])
def shipping():
    error_msg = ""
    session = request.args.get('session')
    id_user = request.args.get('id_user')
    id_order = request.args.get('id_order')
    form = ShippingForm()
    shipping_address = form.shipping_address.data
    params = {
        "id_user": id_user,
        "shipping_address": shipping_address,
        "status": "initiated"
    }
    response = requests.put(DB_PATH + f"/shop-order/{id_order}", json=params)
    if response.json()['result']['msg'] == "ok":
        return redirect(url_for("create_checkout_session", id_user=id_user, id_order=id_order, session=session))
    error_msg = f"update of shipping_address {shipping_address} in order {id_order} failed"
    return render_template("error.html", msg=error_msg)

@app.route('/create-checkout-session')
def create_checkout_session():
    error_msg = ""
    session = request.args.get("session")

    user = {}
    id_user = int(request.args.get("id_user"))
    response = requests.get(DB_PATH + f"/user/{id_user}")
    if response.json()['result']['msg'] == 'ok':
        user = response.json()['data']
    else:
        error_msg = f"user {id_user} not found"

    shop_order = {}
    id_order = int(request.args.get("id_order"))
    response = requests.get(DB_PATH + f"/shop-order/{id_order}")
    if response.json()['result']['msg'] == 'ok':
        shop_order = response.json()['data']
    else:
        error_msg += f"order {id_order} not found"

    if user and shop_order and shop_order["id_user"] == id_user and user["token_expiration_date"] >= date_today():
        success_url = f"http://localhost:5000/success?id_user={id_user}&id_order={id_order}&session={session}"
        cancel_url = f"http://localhost:5000/cancel?id_user={id_user}&session=session"
        try:
            order_lines = []
            shopping_cart_products_ok = True
            for line in shopping_cart[session]:
                quantity = line['quantity']
                id_product = line['id_product']
                response = requests.get(DB_PATH + f"/product/{id_product}")
                if response.json()['result']['msg'] == 'ok':
                    product = response.json()['data']
                else:
                    shopping_cart_products_ok = False
                    error_msg = f"shoppingcart product nok: {id_product}"
                    break
                if run_mode == "test":
                    price = product["id_price_test"]
                else:
                    price = product["id_price_prod"]
                order_lines.append({'price': price, 'quantity': quantity})

            if shopping_cart_products_ok:
                checkout_session = stripe.checkout.Session.create(
                    line_items=order_lines,
                    mode='payment',
                    success_url=success_url,
                    cancel_url=cancel_url
                )
            else:
                return render_template("error.html", msg=error_msg)
        except Exception as e:
            return render_template("error.html", msg=str(e))
        return redirect(checkout_session.url, code=303)
    error_msg="token expired or issue with user and/or order"
    return render_template("error.html", msg=error_msg)


@app.route("/success")
def success():
    session = request.args.get('session')
    id_user = request.args.get('id_user')
    id_order = request.args.get('id_order')
    response = requests.get(DB_PATH + f"/user/{id_user}")
    if response.json()['result']['msg'] == 'ok':
        user = response.json()['data']
        email = user["email"]
        send_invoice(session, email)
        shopping_cart.pop(session)
        response = requests.get(DB_PATH + f"/shop-order/{id_order}")
        if response.json()['result']['msg'] == 'ok':
            shop_order = response.json()['data']
            shop_order["status"] = "paid"
            response = requests.put(DB_PATH + f"/shop-order/{id_order}", json=shop_order)
            if response.json()['result']['msg'] == 'ok':
                create_event("order", id_order, "paid")
                return render_template("success.html", user=user)
            else:
                return render_template("error.html", msg=f"update status to 'paid' failed for order {id_order}")
        else:
            return render_template("error.html", msg=f"shop order {id_order} not found")
    else:
        shopping_cart.pop(session)
        return render_template("error.html", msg=f"user {id_user} not found")


@app.route("/cancel")
def cancel():
    session = request.args.get('session')
    shopping_cart.pop(session)
    id_user = request.args.get('id_user')
    response = requests.get(DB_PATH + f"/user/{id_user}")
    if response.json()['result']['msg'] == 'ok':
        user = response.json()['data']
        return render_template("cancel.html", user=user)
    else:
        return render_template("error.html", msg=f"user {id_user} not found")


@app.route("/get_picture", methods=["GET"])
def get_picture():
    picture = request.args.get('product_picture')
    print("get_picture", picture)
    return send_from_directory("static/images", picture)


if __name__ == "__main__":
    app.run(debug=True)
