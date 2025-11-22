import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Station(db.Model):
    __tablename__ = 'stations'
    stationid = db.Column(db.Integer, primary_key=True)
    stationname = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(255))
    operatorname = db.Column(db.String(120))
    contactno = db.Column(db.String(20))
    isactive = db.Column(db.Boolean, default=True)



class User(db.Model):
    __tablename__ = 'users'
    userid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    userroleid = db.Column(db.Integer)
    stationid = db.Column(db.Integer)
    email = db.Column(db.String(120))

    # ✅ Hash password before saving
    def set_password(self, raw_password):
        hashed = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())
        self.password = hashed.decode('utf-8')

    # ✅ Verify password
    def check_password(self, raw_password):
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password.encode('utf-8'))

class Tank(db.Model):
    __tablename__ = 'tanks'
    tankid = db.Column(db.Integer, primary_key=True)
    stationid = db.Column(db.Integer)
    fueltypeid = db.Column(db.Integer)
    capacity = db.Column(db.Numeric(12,2))
    currentstock = db.Column(db.Numeric(12,2))
    rol = db.Column(db.Numeric(12,2))
    lastinspection = db.Column(db.Date)

class FuelSales(db.Model):
    __tablename__ = "fuelsales"

    fuelsalesid = db.Column(db.Integer, primary_key=True)
    stationid = db.Column(db.Integer, nullable=False)
    fueltypeid = db.Column(db.Integer, nullable=False)
    saledate = db.Column(db.Date, nullable=False)
    volumedispensed = db.Column(db.Float, nullable=False)
    unitprice = db.Column(db.Float, nullable=False)
    salevalue = db.Column("salevalue", db.Float)

class FuelStock(db.Model):
    __tablename__ = 'fuelstock'
    fuelstockid = db.Column(db.Integer, primary_key=True)
    stationid = db.Column(db.Integer)
    tankid = db.Column(db.Integer)
    recorddate = db.Column(db.Date)
    openingstock = db.Column(db.Numeric)
    closingstock = db.Column(db.Numeric)
    expectedstock = db.Column(db.Numeric)
    variance = db.Column(db.Numeric)
    variancepercent = db.Column(db.Numeric)

class Delivery(db.Model):
    __tablename__ = 'fueldeliveries'

    fueldeliveryid = db.Column(db.Integer, primary_key=True)
    stationid = db.Column(db.Integer, nullable=False)
    tankid = db.Column(db.Integer, nullable=False)
    supplierid = db.Column(db.Integer)
    deliverydate = db.Column(db.Date, nullable=False)
    receivedqty = db.Column(db.Numeric(12, 2), nullable=False)

