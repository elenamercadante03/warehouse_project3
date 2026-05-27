from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///stock_manager.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float, nullable=False)


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    operation = db.Column(db.String(100), nullable=False)
    product = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(200), nullable=False)


with app.app_context():
    db.create_all()

    account = Account.query.first()
    if account is None:
        account = Account(balance=7500)
        db.session.add(account)

    monitor = Product.query.filter_by(name="Monitor").first()
    if monitor is None:
        monitor = Product(name="Monitor", quantity=15)
        db.session.add(monitor)

    db.session.commit()


@app.route("/")
def index():
    try:
        products = Product.query.all()
        account = Account.query.first()

        return render_template(
            "index.html",
            warehouse=products,
            balance=account.balance
        )

    except Exception as error:
        return f"Database error: {error}"


@app.route("/purchase/", methods=["GET", "POST"])
def purchase():
    error = None

    if request.method == "POST":
        try:
            product_name = request.form.get("product_name")
            unit_price = float(request.form.get("unit_price"))
            pieces = int(request.form.get("pieces"))

            account = Account.query.first()
            total_price = unit_price * pieces

            if product_name == "" or unit_price <= 0 or pieces <= 0:
                error = "Incorrect purchase data."

            elif account.balance < total_price:
                error = "Not enough money."

            else:
                product = Product.query.filter_by(name=product_name).first()

                if product is None:
                    product = Product(name=product_name, quantity=pieces)
                    db.session.add(product)
                else:
                    product.quantity += pieces

                account.balance -= total_price

                history = History(
                    operation="Purchase",
                    product=product_name,
                    value=f"{pieces} pieces, {unit_price} PLN each"
                )

                db.session.add(history)
                db.session.commit()

                return redirect("/")

        except Exception as error_message:
            db.session.rollback()
            error = f"Error: {error_message}"

    return render_template("purchase.html", error=error)


@app.route("/sale/", methods=["GET", "POST"])
def sale():
    error = None

    if request.method == "POST":
        try:
            product_name = request.form.get("product_name")
            unit_price = float(request.form.get("unit_price"))
            pieces = int(request.form.get("pieces"))

            product = Product.query.filter_by(name=product_name).first()
            account = Account.query.first()

            if product_name == "" or unit_price <= 0 or pieces <= 0:
                error = "Incorrect sale data."

            elif product is None:
                error = "Product does not exist."

            elif product.quantity < pieces:
                error = "Not enough products in warehouse."

            else:
                product.quantity -= pieces
                account.balance += unit_price * pieces

                history = History(
                    operation="Sale",
                    product=product_name,
                    value=f"{pieces} pieces, {unit_price} PLN each"
                )

                db.session.add(history)
                db.session.commit()

                return redirect("/")

        except Exception as error_message:
            db.session.rollback()
            error = f"Error: {error_message}"

    return render_template("sale.html", error=error)


@app.route("/balance/", methods=["GET", "POST"])
def change_balance():
    error = None

    if request.method == "POST":
        try:
            operation_type = request.form.get("operation_type")
            value = float(request.form.get("value"))

            account = Account.query.first()

            if value <= 0:
                error = "Incorrect balance value."

            elif operation_type == "add":
                account.balance += value

                history = History(
                    operation="Balance change",
                    product="-",
                    value=f"Add {value} PLN"
                )

                db.session.add(history)
                db.session.commit()

                return redirect("/")

            elif operation_type == "subtract":
                if account.balance < value:
                    error = "Not enough money."
                else:
                    account.balance -= value

                    history = History(
                        operation="Balance change",
                        product="-",
                        value=f"Subtract {value} PLN"
                    )

                    db.session.add(history)
                    db.session.commit()

                    return redirect("/")

            else:
                error = "Incorrect operation type."

        except Exception as error_message:
            db.session.rollback()
            error = f"Error: {error_message}"

    return render_template("balance.html", error=error)


@app.route("/history/")
@app.route("/history/<int:line_from>/<int:line_to>/")
def history(line_from=None, line_to=None):
    try:
        history_data = History.query.all()

        if line_from is not None and line_to is not None:
            history_data = history_data[line_from:line_to]

        return render_template("history.html", history=history_data)

    except Exception as error:
        return f"Database error: {error}"


if __name__ == "__main__":
    app.run(debug=True)

