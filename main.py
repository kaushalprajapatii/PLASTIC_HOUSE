# import os
# import json
# import urllib.parse
# from datetime import datetime

# from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
# from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates

# from sqlalchemy import create_engine, Column, Integer, String
# from sqlalchemy.orm import sessionmaker, declarative_base

# from fpdf import FPDF

# # ================= CONFIG =================

# SERVER_IP = "127.0.0.1"

# ADMIN_USERNAME = "admin"
# ADMIN_PASSWORD = "plastic123"

# app = FastAPI()

# os.makedirs("static/images", exist_ok=True)
# os.makedirs("static/bills", exist_ok=True)

# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")

# # ================= DATABASE =================

# DATABASE_URL = "sqlite:///./database.db"

# engine = create_engine(
#     DATABASE_URL,
#     connect_args={"check_same_thread": False}
# )

# SessionLocal = sessionmaker(bind=engine)
# Base = declarative_base()

# # ================= MODELS =================

# class Product(Base):
#     __tablename__ = "products"

#     id = Column(Integer, primary_key=True)
#     name = Column(String)
#     price = Column(Integer)
#     stock = Column(Integer)
#     category = Column(String)
#     image = Column(String)


# class Owner(Base):
#     __tablename__ = "owners"

#     id = Column(Integer, primary_key=True)
#     phone = Column(String)


# class Order(Base):
#     __tablename__ = "orders"

#     id = Column(Integer, primary_key=True)
#     shop_name = Column(String)
#     customer_name = Column(String)
#     phone = Column(String)
#     items = Column(String)
#     total = Column(Integer)
#     timestamp = Column(String)


# Base.metadata.create_all(bind=engine)

# cart = {}

# # ================= DB =================

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # ================= ADMIN CHECK =================

# def verify_admin(request: Request):
#     if request.cookies.get("admin") != "true":
#         raise HTTPException(status_code=403)

# # ================= PDF =================

# class BillPDF(FPDF):

#     def header(self):

#         if os.path.exists("static/logo.png"):
#             self.image("static/logo.png", 10, 8, 25)

#         self.set_font("Arial", "B", 16)
#         self.cell(0, 10, "PLASTIC HOUSE", ln=True, align="C")
#         self.ln(10)


# def generate_bill(order):

#     items = json.loads(order.items)

#     pdf = BillPDF()
#     pdf.add_page()

#     pdf.set_font("Arial", size=12)

#     pdf.cell(0, 10, f"Shop: {order.shop_name}", ln=True)
#     pdf.cell(0, 10, f"Customer: {order.customer_name}", ln=True)
#     pdf.cell(0, 10, f"Phone: {order.phone}", ln=True)
#     pdf.cell(0, 10, f"Date: {order.timestamp}", ln=True)

#     pdf.ln(5)

#     pdf.set_font("Arial", "B", 12)

#     pdf.cell(70, 10, "Item", 1)
#     pdf.cell(30, 10, "Qty", 1)
#     pdf.cell(40, 10, "Price", 1)
#     pdf.cell(40, 10, "Total", 1)
#     pdf.ln()

#     pdf.set_font("Arial", size=11)

#     for name, data in items.items():

#         pdf.cell(70, 10, name, 1)
#         pdf.cell(30, 10, str(data["qty"]), 1)
#         pdf.cell(40, 10, str(data["price"]), 1)
#         pdf.cell(40, 10, str(data["qty"] * data["price"]), 1)
#         pdf.ln()

#     path = f"static/bills/bill_{order.id}.pdf"
#     pdf.output(path)

#     return path

# # ================= ADMIN LOGIN =================

# @app.get("/admin", response_class=HTMLResponse)
# def admin_login_page(request: Request):
#     return templates.TemplateResponse("admin_login.html", {"request": request})


# @app.post("/admin_login")
# def admin_login(username: str = Form(...), password: str = Form(...)):

#     if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
#         response = RedirectResponse("/admin/dashboard", status_code=302)
#         response.set_cookie("admin", "true")
#         return response

#     return RedirectResponse("/admin", status_code=302)

# # ================= HOME =================

# @app.get("/", response_class=HTMLResponse)
# def home(request: Request, db=Depends(get_db)):

#     products = db.query(Product).all()

#     categories = {}
#     for p in products:
#         categories.setdefault(p.category.capitalize(), []).append(p)

#     return templates.TemplateResponse(
#         "home.html",
#         {"request": request, "products": categories}
#     )

# # ================= CATEGORY =================

# @app.get("/category/{cat}", response_class=HTMLResponse)
# def category(request: Request, cat: str, db=Depends(get_db)):

#     items = db.query(Product).filter(Product.category == cat.lower()).all()

#     return templates.TemplateResponse(
#         "category.html",
#         {"request": request, "items": items, "cat": cat.capitalize()}
#     )

# # ================= CART =================

# @app.post("/add_to_cart")
# async def add_to_cart(item: str = Form(...), qty: int = Form(...), price: int = Form(...), image: str = Form(...)):

#     if qty <= 0:
#         return {"message": "Select quantity"}

#     if item in cart:
#         cart[item]["qty"] += qty
#     else:
#         cart[item] = {"qty": qty, "price": price, "image": image}

#     return {"message": "Added to cart"}


# @app.get("/delete_cart/{item}")
# def delete_cart(item: str):
#     cart.pop(item, None)
#     return RedirectResponse("/cart", status_code=302)


# @app.get("/cart", response_class=HTMLResponse)
# def view_cart(request: Request):

#     total = sum(v["qty"] * v["price"] for v in cart.values())

#     return templates.TemplateResponse(
#         "cart.html",
#         {"request": request, "cart": cart, "total": total}
#     )

# # ================= PAYMENT =================

# @app.get("/payment", response_class=HTMLResponse)
# def payment(request: Request):

#     total = sum(v["qty"] * v["price"] for v in cart.values())

#     return templates.TemplateResponse(
#         "payment.html",
#         {"request": request, "cart": cart, "total": total}
#     )

# # ================= PLACE ORDER =================

# @app.post("/place_order")
# async def place_order(
#         shop_name: str = Form(...),
#         customer_name: str = Form(...),
#         phone: str = Form(...),
#         db=Depends(get_db)
# ):

#     if not cart:
#         return RedirectResponse("/cart", status_code=302)

#     if not phone.startswith("91"):
#         phone = "91" + phone

#     timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")

#     total = sum(v["qty"] * v["price"] for v in cart.values())

#     order = Order(
#         shop_name=shop_name,
#         customer_name=customer_name,
#         phone=phone,
#         items=json.dumps(cart),
#         total=total,
#         timestamp=timestamp
#     )

#     db.add(order)

#     for item, data in cart.items():
#         product = db.query(Product).filter(Product.name == item).first()
#         if product:
#             product.stock -= data["qty"]

#     db.commit()
#     db.refresh(order)

#     pdf_path = generate_bill(order)
#     bill_link = f"http://{SERVER_IP}:8000/{pdf_path}"

#     # owners = db.query(Owner).all()

#     # for o in owners:
#     #     msg = urllib.parse.quote(f"New Order\nBill: {bill_link}")
#     #     owner_url = f"https://wa.me/{o.phone}?text={msg}"

#     owners = db.query(Owner).all()

#     if owners:
#         for o in owners:
#             msg = urllib.parse.quote(f"New Order\nBill: {bill_link}")
#             owner_url = f"https://wa.me/{o.phone}?text={msg}"


#     cust_msg = urllib.parse.quote(f"Thank you {customer_name}\nBill: {bill_link}")
#     customer_url = f"https://wa.me/{phone}?text={cust_msg}"

#     cart.clear()

#     return RedirectResponse(customer_url, status_code=302)

# # ================= PRODUCT UPLOAD =================

# @app.post("/admin/upload")
# async def upload_product(
#         name: str = Form(...),
#         price: int = Form(...),
#         stock: int = Form(...),
#         category: str = Form(...),
#         image: UploadFile = File(...),
#         db=Depends(get_db),
#         _: None = Depends(verify_admin)
# ):

#     filepath = f"static/images/{image.filename}"

#     with open(filepath, "wb") as buffer:
#         buffer.write(await image.read())

#     db.add(Product(
#         name=name,
#         price=price,
#         stock=stock,
#         category=category.lower(),
#         image=image.filename
#     ))

#     db.commit()

#     return RedirectResponse("/admin/dashboard", status_code=302)

# # ================= ADMIN DASHBOARD =================

# @app.get("/admin/dashboard", response_class=HTMLResponse)
# def admin_dashboard(
#         request: Request,
#         db=Depends(get_db),
#         _: None = Depends(verify_admin)
# ):

#     products = db.query(Product).all()

#     return templates.TemplateResponse(
#         "admin_dashboard.html",
#         {"request": request, "products": products}
#     )

# # ================= OWNER MANAGEMENT =================

# @app.get("/admin/owners", response_class=HTMLResponse)
# def owners_page(
#         request: Request,
#         db=Depends(get_db),
#         _: None = Depends(verify_admin)
# ):

#     owners = db.query(Owner).all()

#     return templates.TemplateResponse(
#         "owners.html",
#         {"request": request, "owners": owners}
#     )


# @app.post("/admin/add_owner")
# def add_owner(phone: str = Form(...), db=Depends(get_db)):

#     if not phone.startswith("91"):
#         phone = "91" + phone

#     db.add(Owner(phone=phone))
#     db.commit()

#     return RedirectResponse("/admin/owners", status_code=302)


# @app.get("/admin/delete_owner/{oid}")
# def delete_owner(oid: int, db=Depends(get_db)):

#     owner = db.query(Owner).filter(Owner.id == oid).first()

#     if owner:
#         db.delete(owner)
#         db.commit()

#     return RedirectResponse("/admin/owners", status_code=302)

# # ================= DOWNLOAD BILL =================

# @app.get("/download/{order_id}")
# def download_bill(order_id: int):
#     return FileResponse(f"static/bills/bill_{order_id}.pdf")








# ========= IMPORTS =========

import os
import json
import urllib.parse
import random
from datetime import datetime

from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

from fpdf import FPDF

# ========= CONFIG =========

SERVER_IP = "127.0.0.1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "plastic123"

app = FastAPI()

os.makedirs("static/images", exist_ok=True)
os.makedirs("static/bills", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ========= DATABASE =========

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ========= MODELS =========

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)
    stock = Column(Integer)
    sold = Column(Integer, default=0)
    category = Column(String)
    media = Column(String)  # JSON list


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    phone = Column(String, unique=True)
    password = Column(String)


class Owner(Base):
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True)
    phone = Column(String)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    shop_name = Column(String)
    customer_name = Column(String)
    phone = Column(String)
    items = Column(String)
    total = Column(Integer)
    payment_mode = Column(String)
    status = Column(String, default="Pending")
    timestamp = Column(String)


Base.metadata.create_all(bind=engine)

cart = {}
otp_store = {}

# ========= DB =========

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========= SESSION =========

def verify_user(request: Request):
    if not request.cookies.get("user"):
        raise HTTPException(403)

def verify_admin(request: Request):
    if request.cookies.get("admin") != "true":
        raise HTTPException(403)

# ========= AUTH =========

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(username: str = Form(...), phone: str = Form(...), password: str = Form(...), db=Depends(get_db)):

    if db.query(User).filter(User.username == username).first():
        return RedirectResponse("/register", 302)

    db.add(User(username=username, phone=phone, password=password))
    db.commit()

    return RedirectResponse("/login", 302)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), db=Depends(get_db)):

    user = db.query(User).filter(User.username == username, User.password == password).first()

    if user:
        res = RedirectResponse("/", 302)
        res.set_cookie("user", username)
        return res

    return RedirectResponse("/login", 302)


@app.get("/logout")
def logout():
    res = RedirectResponse("/", 302)
    res.delete_cookie("user")
    return res


# OTP LOGIN

@app.post("/send_otp")
def send_otp(phone: str = Form(...)):
    otp = str(random.randint(1000, 9999))
    otp_store[phone] = otp
    print("OTP:", otp)
    return {"msg": "OTP sent"}

@app.post("/verify_otp")
def verify_otp(phone: str = Form(...), otp: str = Form(...)):
    if otp_store.get(phone) == otp:
        res = RedirectResponse("/", 302)
        res.set_cookie("user", phone)
        return res
    return RedirectResponse("/login", 302)

# ========= HOME =========

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db=Depends(get_db)):

    products = db.query(Product).all()

    categories = {}
    for p in products:
        media = json.loads(p.media) if p.media else []
        categories.setdefault(p.category.capitalize(), []).append({**p.__dict__, "media": media})

    return templates.TemplateResponse("home.html", {"request": request, "products": categories})

# ========= CATEGORY =========

@app.get("/category/{cat}", response_class=HTMLResponse)
def category(request: Request, cat: str, db=Depends(get_db)):

    items = db.query(Product).filter(Product.category == cat.lower()).all()

    result = []
    for p in items:
        result.append({**p.__dict__, "media": json.loads(p.media) if p.media else []})

    return templates.TemplateResponse("category.html", {"request": request, "items": result, "cat": cat.capitalize()})

# ========= CART =========

@app.post("/add_to_cart")
async def add_to_cart(item: str = Form(...), qty: int = Form(...), price: int = Form(...), image: str = Form(...)):

    if item in cart:
        cart[item]["qty"] += qty
    else:
        cart[item] = {"qty": qty, "price": price, "image": image}

    return {"message": "Added to cart"}

@app.get("/cart", response_class=HTMLResponse)
def cart_page(request: Request):
    total = sum(v["qty"] * v["price"] for v in cart.values())
    return templates.TemplateResponse("cart.html", {"request": request, "cart": cart, "total": total})

# ========= PAYMENT =========

@app.get("/payment", response_class=HTMLResponse)
def payment(request: Request):
    total = sum(v["qty"] * v["price"] for v in cart.values())
    return templates.TemplateResponse("payment.html", {"request": request, "cart": cart, "total": total})

# ========= BILL PDF =========

class BillPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 18)
        self.cell(0, 10, "PLASTIC HOUSE", ln=True, align="C")
        self.ln(5)

def generate_bill(order):

    pdf = BillPDF()
    pdf.add_page()

    items = json.loads(order.items)

    pdf.set_font("Arial", size=12)

    pdf.cell(0, 8, f"Shop : {order.shop_name}", ln=True)
    pdf.cell(0, 8, f"Customer : {order.customer_name}", ln=True)
    pdf.cell(0, 8, f"Payment : {order.payment_mode}", ln=True)
    pdf.cell(0, 8, f"Date : {order.timestamp}", ln=True)

    pdf.ln(5)

    for name, data in items.items():
        pdf.cell(0, 8, f"{name} x {data['qty']} = Rs. {data['qty']*data['price']}", ln=True)

    pdf.ln(5)
    pdf.cell(0, 10, f"Total Rs. {order.total}", ln=True)

    filename = f"{order.shop_name}_{order.id}.pdf".replace(" ", "_")
    path = f"static/bills/{filename}"

    pdf.output(path)
    return path

# ========= PLACE ORDER =========

@app.post("/place_order")
async def place_order(request: Request, shop_name: str = Form(...), customer_name: str = Form(...), phone: str = Form(...), pay: str = Form(...), db=Depends(get_db)):

    username = request.cookies.get("user")

    if not cart:
        return RedirectResponse("/cart", 302)

    total = sum(v["qty"] * v["price"] for v in cart.values())

    order = Order(
        username=username,
        shop_name=shop_name,
        customer_name=customer_name,
        phone=phone,
        items=json.dumps(cart),
        total=total,
        payment_mode=pay,
        timestamp=datetime.now().strftime("%d-%m-%Y %H:%M")
    )

    db.add(order)

    for item, data in cart.items():
        p = db.query(Product).filter(Product.name == item).first()
        if p:
            p.stock -= data["qty"]
            p.sold += data["qty"]

    db.commit()

    generate_bill(order)
    cart.clear()

    return RedirectResponse("/orders", 302)

# ========= CUSTOMER ORDERS =========

@app.get("/my_orders", response_class=HTMLResponse)
def order_history(request: Request, db=Depends(get_db), _: None = Depends(verify_user)):

    username = request.cookies.get("user")

    orders_db = db.query(Order).filter(Order.username == username).all()

    # Convert JSON items
    orders = []
    for o in orders_db:
        orders.append({
            **o.__dict__,
            "items": json.loads(o.items)
        })

    return templates.TemplateResponse(
        "order_history.html",
        {"request": request, "orders": orders}
    )


# ========= OWNER ORDERS =========

@app.get("/admin/orders", response_class=HTMLResponse)
def owner_orders(request: Request, db=Depends(get_db), _: None = Depends(verify_admin)):

    pending_db = db.query(Order).filter(Order.status == "Pending").all()
    delivered_db = db.query(Order).filter(Order.status == "Delivered").all()

    # Convert JSON items → dictionary
    pending = []
    for o in pending_db:
        pending.append({**o.__dict__, "items": json.loads(o.items)})

    delivered = []
    for o in delivered_db:
        delivered.append({**o.__dict__, "items": json.loads(o.items)})

    return templates.TemplateResponse(
        "order_view.html",
        {"request": request, "pending": pending, "delivered": delivered}
    )


@app.get("/admin/deliver/{oid}")
def mark_delivered(oid: int, db=Depends(get_db)):
    order = db.query(Order).filter(Order.id == oid).first()
    order.status = "Delivered"
    db.commit()
    return RedirectResponse("/admin/orders", 302)

# ========= ADMIN PRODUCT UPLOAD =========

@app.post("/admin/upload")
async def upload_product(name: str = Form(...), price: int = Form(...), stock: int = Form(...), category: str = Form(...), media_files: list[UploadFile] = File(...), db=Depends(get_db), _: None = Depends(verify_admin)):

    media = []

    for file in media_files:
        path = f"static/images/{file.filename}"
        with open(path, "wb") as f:
            f.write(await file.read())
        media.append(file.filename)

    db.add(Product(name=name, price=price, stock=stock, category=category.lower(), media=json.dumps(media)))
    db.commit()

    return RedirectResponse("/admin/dashboard", 302)

# ========= ADMIN LOGIN =========

@app.get("/admin", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/admin_login")
def admin_login(username: str = Form(...), password: str = Form(...)):

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        response = RedirectResponse("/admin/dashboard", status_code=302)
        response.set_cookie("admin", "true")
        return response

    return RedirectResponse("/admin", status_code=302)

# ========= ADMIN DASHBOARD =========

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, db=Depends(get_db), _: None = Depends(verify_admin)):

    products = db.query(Product).all()

    # Convert media JSON → list
    result = []
    for p in products:
        result.append({
            **p.__dict__,
            "media": json.loads(p.media) if p.media else []
        })

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "products": result}
    )

# ========= OWNER MANAGEMENT =========

@app.get("/admin/owners", response_class=HTMLResponse)
def owners_page(request: Request, db=Depends(get_db), _: None = Depends(verify_admin)):

    owners = db.query(Owner).all()

    return templates.TemplateResponse(
        "owners.html",
        {"request": request, "owners": owners}
    )


@app.post("/admin/add_owner")
def add_owner(phone: str = Form(...), db=Depends(get_db)):

    if not phone.startswith("91"):
        phone = "91" + phone

    db.add(Owner(phone=phone))
    db.commit()

    return RedirectResponse("/admin/owners", status_code=302)


@app.get("/admin/delete_owner/{oid}")
def delete_owner(oid: int, db=Depends(get_db)):

    owner = db.query(Owner).filter(Owner.id == oid).first()

    if owner:
        db.delete(owner)
        db.commit()

    return RedirectResponse("/admin/owners", status_code=302)


# ========= DOWNLOAD BILL =========

@app.get("/download/{order_id}")
def download_bill(order_id: int):

    # Find bill file inside static/bills
    for file in os.listdir("static/bills"):
        if file.endswith(f"_{order_id}.pdf"):
            path = f"static/bills/{file}"
            return FileResponse(path, filename=file)

    raise HTTPException(status_code=404, detail="Bill not found")
