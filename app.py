from ast import Import
from datetime import datetime, timedelta
import bcrypt
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from models import Delivery, FuelSales, FuelStock, Tank, db, Station, User
import config

app = Flask(__name__)
app.config.from_object(config)

# ✅ DB + CORS + JWT setup
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://fuel_admin:FuelAdmin123@localhost/fuel_management'
app.config['JWT_SECRET_KEY'] = 'supersecretjwtkey'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=4)
import os
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")

db.init_app(app)
CORS(app)
jwt = JWTManager(app)


@app.route('/')
def home():
    return "✅ Fuel Management API Running"

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
    #     return jsonify({"msg": "Invalid credentials"}), 401

    token = create_access_token(identity=user.username)
    return jsonify({
        "token": token,
        "username": user.username,
        "role": user.userroleid
    })

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    userroleid = data.get("userroleid", 1)  # Default to 1 (e.g. Admin or Operator)

    # Validate fields
    if not username or not email or not password:
        return jsonify({"msg": "All fields are required"}), 400

    # Check if user already exists
    existing = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing:
        return jsonify({"msg": "User already exists"}), 409

    # Hash password using bcrypt
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Create new user
    new_user = User(username=username, email=email, password=hashed_pw, userroleid=userroleid)
    db.session.add(new_user)
    db.session.commit()

    # Auto-login after registration (optional)
    token = create_access_token(identity=username)

    return jsonify({
        "msg": "User registered successfully",
        "token": token,
        "username": username,
        "role": userroleid
    }), 201


@app.route('/stations', methods=['GET'])
@jwt_required()
def get_stations():
    stations = Station.query.all()
    return jsonify([
        {
            "StationID": s.stationid,
            "StationName": s.stationname,
            "Location": s.location,
            "OperatorName": s.operatorname,
            "ContactNo": s.contactno
        } for s in stations
    ])

@app.route('/tanks', methods=['GET'])
@jwt_required()
def get_tanks():
    tanks = Tank.query.all()
    return jsonify([
        {
            "TankID": t.tankid,
            "StationID": t.stationid,
            "FuelTypeID": t.fueltypeid,
            "Capacity": float(t.capacity),
            "CurrentStock": float(t.currentstock),
            "ROL": float(t.rol),
            "LastInspection": str(t.lastinspection)
        } for t in tanks
    ])

# @app.route('/fuelsales', methods=['GET'])
# @jwt_required()
# def get_sales():
#     sales = FuelSales.query.all()
#     return jsonify([
#         {
#             "FuelSalesID": f.fuelsalesid,
#             "StationID": f.stationid,
#             "FuelTypeID": f.fueltypeid,
#             "SaleDate": str(f.saledate),
#             "VolumeDispensed": float(f.volumedispensed),
#             "UnitPrice": float(f.unitprice),
#             "SaleValue": float(f.salevalue)
#         } for f in sales
#     ])

# @app.route('/fuelstock', methods=['GET'])
# @jwt_required()
# def get_stock():
#     stock = FuelStock.query.all()
#     return jsonify([
#         {
#             "FuelStockID": fs.fuelstockid,
#             "StationID": fs.stationid,
#             "TankID": fs.tankid,
#             "RecordDate": str(fs.recorddate),
#             "OpeningStock": float(fs.openingstock),
#             "ClosingStock": float(fs.closingstock),
#             "ExpectedStock": float(fs.expectedstock),
#             "Variance": float(fs.variance),
#             "VariancePercent": float(fs.variancepercent)
#         } for fs in stock
#     ])

# ----------------------------------------
#  FUELS SALES CRUD
# ----------------------------------------
@app.route('/fuelsales', methods=['GET'])
@jwt_required()
def get_sales():
    sales = FuelSales.query.all()
    return jsonify([
        {
            "FuelSalesID": f.fuelsalesid,
            "StationID": f.stationid,
            "FuelTypeID": f.fueltypeid,
            "SaleDate": str(f.saledate),
            "VolumeDispensed": float(f.volumedispensed),
            "UnitPrice": float(f.unitprice),
            "SaleValue": float(f.salevalue)
        } for f in sales
    ])

@app.route('/fuelsales', methods=['POST'])
@jwt_required()
def add_sale():
    data = request.get_json()
    try:
        sale = FuelSales(
            stationid=data['StationID'],
            fueltypeid=data['FuelTypeID'],
            saledate=data['SaleDate'],
            volumedispensed=data['VolumeDispensed'],
            unitprice=data['UnitPrice'],
            salevalue=data['SaleValue']
        )
        db.session.add(sale)
        db.session.commit()
        return jsonify({"msg": "Sale added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/fuelsales/<int:id>', methods=['PUT'])
@jwt_required()
def update_sale(id):
    sale = FuelSales.query.get_or_404(id)
    data = request.get_json()
    try:
        sale.stationid = data.get('StationID', sale.stationid)
        sale.fueltypeid = data.get('FuelTypeID', sale.fueltypeid)
        sale.saledate = data.get('SaleDate', sale.saledate)
        sale.volumedispensed = data.get('VolumeDispensed', sale.volumedispensed)
        sale.unitprice = data.get('UnitPrice', sale.unitprice)
        sale.salevalue = data.get('SaleValue', sale.salevalue)
        db.session.commit()
        return jsonify({"msg": "Sale updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/fuelsales/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_sale(id):
    sale = FuelSales.query.get_or_404(id)
    try:
        db.session.delete(sale)
        db.session.commit()
        return jsonify({"msg": "Sale deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ----------------------------------------
#  FUEL STOCK CRUD
# ----------------------------------------
@app.route('/fuelstock', methods=['GET'])
@jwt_required()
def get_stock():
    stock = FuelStock.query.all()
    return jsonify([
        {
            "FuelStockID": fs.fuelstockid,
            "StationID": fs.stationid,
            "TankID": fs.tankid,
            "RecordDate": str(fs.recorddate),
            "OpeningStock": float(fs.openingstock),
            "ClosingStock": float(fs.closingstock),
            "ExpectedStock": float(fs.expectedstock),
            "Variance": float(fs.variance),
            "VariancePercent": float(fs.variancepercent)
        } for fs in stock
    ])

def _required(body, key, cast=None):
    if key not in body or body[key] in (None, ""):
        raise ValueError(f"{key} is required")
    return cast(body[key]) if cast else body[key]

@app.route("/fuelsales", methods=["POST"])
@jwt_required()
def create_fuelsale():
    try:
        body = request.get_json() or {}
        stationid = _required(body, "StationID", int)
        fueltypeid = _required(body, "FuelTypeID", int)
        vol = _required(body, "VolumeDispensed", float)
        price = _required(body, "UnitPrice", float)
        saledate_str = _required(body, "SaleDate", str)

        # parse date (accepts "YYYY-MM-DD")
        saledate = datetime.strptime(saledate_str, "%Y-%m-%d").date()

        salevalue = vol * price

        rec = FuelSales(
            stationid=stationid,
            fueltypeid=fueltypeid,
            saledate=saledate,
            volumedispensed=vol,
            unitprice=price,
            salevalue=salevalue,
        )
        db.session.add(rec)
        db.session.commit()

        return {
            "FuelSalesID": rec.fuelsalesid,
            "StationID": rec.stationid,
            "FuelTypeID": rec.fueltypeid,
            "SaleDate": rec.saledate.isoformat(),
            "VolumeDispensed": float(rec.volumedispensed),
            "UnitPrice": float(rec.unitprice),
            "SaleValue": float(rec.salevalue),
        }, 201

    except ValueError as ve:
        db.session.rollback()
        return {"msg": str(ve)}, 400
    except Exception as e:
        db.session.rollback()
        return {"msg": "Failed to create fuel sale", "error": str(e)}, 500


@app.route("/fuelsales/<int:sale_id>", methods=["PUT"])
@jwt_required()
def update_fuelsale(sale_id):
    try:
        rec = FuelSales.query.get_or_404(sale_id)
        body = request.get_json() or {}

        # allow partial update; validate if present
        if "StationID" in body:
            rec.stationid = int(body["StationID"])
        if "FuelTypeID" in body:
            rec.fueltypeid = int(body["FuelTypeID"])
        if "VolumeDispensed" in body:
            rec.volumedispensed = float(body["VolumeDispensed"])
        if "UnitPrice" in body:
            rec.unitprice = float(body["UnitPrice"])
        if "SaleDate" in body and body["SaleDate"]:
            rec.saledate = datetime.strptime(body["SaleDate"], "%Y-%m-%d").date()

        # recalc sale value whenever vol/price changed
        if rec.volumedispensed is not None and rec.unitprice is not None:
            rec.salevalue = float(rec.volumedispensed) * float(rec.unitprice)

        db.session.commit()

        return {
            "FuelSalesID": rec.fuelsalesid,
            "StationID": rec.stationid,
            "FuelTypeID": rec.fueltypeid,
            "SaleDate": rec.saledate.isoformat(),
            "VolumeDispensed": float(rec.volumedispensed),
            "UnitPrice": float(rec.unitprice),
            "SaleValue": float(rec.salevalue),
        }, 200

    except Exception as e:
        db.session.rollback()
        return {"msg": "Failed to update fuel sale", "error": str(e)}, 500

@app.route('/fuelstock/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_stock(id):
    stock = FuelStock.query.get_or_404(id)
    try:
        db.session.delete(stock)
        db.session.commit()
        return jsonify({"msg": "Stock deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ----------------------------------------
#  DELIVERIES CRUD
# ----------------------------------------
@app.route("/fueldeliveries", methods=["GET"])
def get_deliveries():
    rows = Delivery.query.all()
    return jsonify([
        {
            "FuelDeliveryID": d.fueldeliveryid,
            "StationID": d.stationid,
            "TankID": d.tankid,
            "SupplierID": d.supplierid,
            "DeliveryDate": d.deliverydate.isoformat(),
            "ReceivedQty": float(d.receivedqty)
        } for d in rows
    ])

@app.route("/fueldeliveries", methods=["POST"])
@jwt_required()
def create_fuel_delivery():
    try:
        body = request.get_json() or {}

        stationid = body["StationID"]
        tankid = body["TankID"]
        supplierid = body.get("SupplierID")
        receivedqty = float(body["ReceivedQty"])
        deliverydate_str = body["DeliveryDate"]

        deliverydate = datetime.strptime(deliverydate_str, "%Y-%m-%d").date()

        rec = Delivery(
            stationid=stationid,
            tankid=tankid,
            supplierid=supplierid,
            receivedqty=receivedqty,
            deliverydate=deliverydate,
        )

        db.session.add(rec)
        db.session.commit()

        return jsonify({
            "FuelDeliveryID": rec.fueldeliveryid,
            "StationID": rec.stationid,
            "TankID": rec.tankid,
            "SupplierID": rec.supplierid,
            "DeliveryDate": rec.deliverydate.isoformat(),
            "ReceivedQty": float(rec.receivedqty)
        }), 201

    except KeyError as e:
        db.session.rollback()
        return {"msg": f"Missing required field: {e.args[0]}"}, 400
    except Exception as e:
        db.session.rollback()
        return {"msg": "Failed to create fuel delivery", "error": str(e)}, 500

@app.route("/fueldeliveries/<int:id>", methods=["PUT"])
@jwt_required()
def update_fuel_delivery(id):
    try:
        body = request.get_json() or {}

        delivery = Delivery.query.get(id)
        if not delivery:
            return jsonify({"msg": "Delivery not found"}), 404

        # Update only provided fields
        if "StationID" in body:
            delivery.stationid = body["StationID"]
        if "TankID" in body:
            delivery.tankid = body["TankID"]
        if "SupplierID" in body:
            delivery.supplierid = body["SupplierID"]
        if "ReceivedQty" in body:
            delivery.receivedqty = float(body["ReceivedQty"])
        if "DeliveryDate" in body:
            delivery.deliverydate = datetime.strptime(body["DeliveryDate"], "%Y-%m-%d").date()

        db.session.commit()

        return jsonify({
            "FuelDeliveryID": delivery.fueldeliveryid,
            "StationID": delivery.stationid,
            "TankID": delivery.tankid,
            "SupplierID": delivery.supplierid,
            "DeliveryDate": delivery.deliverydate.isoformat(),
            "ReceivedQty": float(delivery.receivedqty)
        }), 200

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"msg": f"Invalid value: {ve}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to update delivery", "error": str(e)}), 500

@app.route("/fueldeliveries/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_fuel_delivery(id):
    try:
        delivery = Delivery.query.get(id)
        if not delivery:
            return jsonify({"msg": "Delivery not found"}), 404

        db.session.delete(delivery)
        db.session.commit()
        return jsonify({"msg": "Delivery deleted"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to delete delivery", "error": str(e)}), 500
@app.route("/fuelstock", methods=["POST"])
@jwt_required()
def create_fuel_stock():
    data = request.get_json()
    record = FuelStock(
        stationid=data["StationID"],
        tankid=data["TankID"],
        recorddate=datetime.strptime(data["RecordDate"], "%Y-%m-%d").date(),
        openingstock=data["OpeningStock"],
        closingstock=data["ClosingStock"],
        expectedstock=data["ExpectedStock"],
        variance=data.get("Variance", 0),
        variancepercent=data.get("VariancePercent", 0),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"FuelStockID": record.fuelstockid}), 201


@app.route("/fuelstock/<int:id>", methods=["PUT"])
@jwt_required()
def update_fuel_stock(id):
    data = request.get_json()
    record = FuelStock.query.get(id)
    if not record:
        return jsonify({"msg": "Record not found"}), 404

    for field, value in data.items():
        setattr(record, field.lower(), value)
    db.session.commit()
    return jsonify({"msg": "Updated successfully"}), 200


@app.route("/fuelstock/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_fuel_stock(id):
    record = FuelStock.query.get(id)
    if not record:
        return jsonify({"msg": "Not found"}), 404
    db.session.delete(record)
    db.session.commit()
    return jsonify({"msg": "Deleted"}), 200

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)
if __name__ == "__main__":
    app.run()



