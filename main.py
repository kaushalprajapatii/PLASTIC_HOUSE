import os
import json
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

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "plastic123"

app = FastAPI()

@app.middleware("http")
async def disable_cache(request, call_next):
    response = await call_next(request)

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


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
    media = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    phone = Column(String, unique=True)
    password = Column(String)

class Owner(Base):
    __tablename__ = "owners"
    id = Column(Integer, primary_key=True)
    name = Column(String)
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

# ========= SESSION =========

cart_store = {}
otp_store = {}

def get_user_cart(username):
    if username not in cart_store:
        cart_store[username] = {}
    return cart_store[username]

# ========= DB =========

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========= AUTH HELPERS =========

def verify_admin(request: Request):
    if request.cookies.get("admin") != "true":
        raise HTTPException(403)

def verify_user(request: Request):
    if not request.cookies.get("user"):
        raise HTTPException(403)

# ========= OTP LOGIN =========

@app.post("/send_otp")
def send_otp(phone: str = Form(...), db=Depends(get_db)):

    user = db.query(User).filter(User.phone == phone).first()

    if not user:
        raise HTTPException(400, "Phone not registered")

    otp = str(random.randint(1000, 9999))
    otp_store[phone] = otp

    print("OTP:", otp)  # TEMP console OTP

    return {"msg": "OTP sent"}

@app.post("/verify_otp")
def verify_otp(phone: str = Form(...), otp: str = Form(...), db=Depends(get_db)):

    if otp_store.get(phone) != otp:
        return RedirectResponse("/login", 302)

    user = db.query(User).filter(User.phone == phone).first()

    res = RedirectResponse("/", 302)
    res.set_cookie("user", user.username)

    return res

# ========= ADMIN =========

@app.get("/admin", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin_login")
def admin_login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        res = RedirectResponse("/admin/dashboard", 302)
        res.set_cookie("admin", "true")
        return res
    return RedirectResponse("/admin", 302)

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, db=Depends(get_db), _: None = Depends(verify_admin)):

    products = db.query(Product).all()

    result = []
    for p in products:
        result.append({**p.__dict__, "media": json.loads(p.media) if p.media else []})

    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "products": result})

@app.post("/admin/upload")
async def upload_product(
    name: str = Form(...),
    price: int = Form(...),
    stock: int = Form(...),
    category: str = Form(...),
    media: list[UploadFile] = File(...),
    db=Depends(get_db),
    _: None = Depends(verify_admin)
):

    media_files = []

    for file in media:
        filename = file.filename
        path = f"static/images/{filename}"

        with open(path, "wb") as f:
            f.write(await file.read())

        media_files.append(filename)

    product = Product(
        name=name,
        price=price,
        stock=stock,
        category=category.lower(),
        media=json.dumps(media_files)
    )

    db.add(product)
    db.commit()

    return RedirectResponse("/admin/dashboard", status_code=302)


@app.get("/admin/owners", response_class=HTMLResponse)
def owners_page(request: Request, db=Depends(get_db), _: None = Depends(verify_admin)):
    owners = db.query(Owner).all()
    return templates.TemplateResponse("owners.html", {"request": request, "owners": owners})

@app.post("/admin/add_owner")
def add_owner(name: str = Form(...), phone: str = Form(...), db=Depends(get_db)):

    db.add(Owner(name=name, phone=phone))
    db.commit()

    return RedirectResponse("/admin/owners", status_code=302)


@app.get("/admin/delete_owner/{oid}")
def delete_owner(oid: int, db=Depends(get_db), _: None = Depends(verify_admin)):

    owner = db.query(Owner).filter(Owner.id == oid).first()

    if owner:
        db.delete(owner)
        db.commit()

    return RedirectResponse("/admin/owners", status_code=302)



@app.get("/admin/orders", response_class=HTMLResponse)
def owner_orders(request: Request, db=Depends(get_db), _: None = Depends(verify_admin)):

    pending_db = db.query(Order).filter(Order.status == "Pending").all()
    delivered_db = db.query(Order).filter(Order.status == "Delivered").all()

    pending = [{**o.__dict__, "items": json.loads(o.items)} for o in pending_db]
    delivered = [{**o.__dict__, "items": json.loads(o.items)} for o in delivered_db]

    return templates.TemplateResponse("order_view.html",
                                      {"request": request, "pending": pending, "delivered": delivered})

@app.get("/admin/delete_product/{pid}")
def delete_product(pid: int, db=Depends(get_db), _: None = Depends(verify_admin)):

    product = db.query(Product).filter(Product.id == pid).first()

    if product:

        # Delete media files
        if product.media:
            media_list = json.loads(product.media)

            for file in media_list:
                path = f"static/images/{file}"
                if os.path.exists(path):
                    os.remove(path)

        db.delete(product)
        db.commit()

    return RedirectResponse("/admin/dashboard", status_code=302)


@app.get("/admin/deliver/{oid}")
def mark_delivered(oid: int, db=Depends(get_db)):
    order = db.query(Order).filter(Order.id == oid).first()
    order.status = "Delivered"
    db.commit()
    return RedirectResponse("/admin/orders", 302)

# ========= LANDING PAGE =========

@app.get("/start", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


# ========= AUTH =========

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

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(username: str = Form(...),
             phone: str = Form(...),
             password: str = Form(...),
             db=Depends(get_db)):

    # Prevent duplicate username or phone
    if db.query(User).filter(User.username == username).first():
        return RedirectResponse("/register", 302)

    if db.query(User).filter(User.phone == phone).first():
        return RedirectResponse("/register", 302)

    new_user = User(username=username, phone=phone, password=password)

    db.add(new_user)
    db.commit()

    return RedirectResponse("/login", 302)


@app.get("/logout")
def logout():
    res = RedirectResponse("/start", 302)
    res.delete_cookie("user")
    res.delete_cookie("admin")
    return res



# ========= HOME =========

@app.get("/", response_class=HTMLResponse)
def root_redirect(request: Request):

    if not request.cookies.get("user"):
        return RedirectResponse("/start")

    return RedirectResponse("/home")


@app.get("/home", response_class=HTMLResponse)
def home(request: Request, db=Depends(get_db)):

    if not request.cookies.get("user"):
        return RedirectResponse("/login")

    products = db.query(Product).all()

    categories = {}
    for p in products:
        media = json.loads(p.media) if p.media else []
        categories.setdefault(p.category.capitalize(), []).append(
            {**p.__dict__, "media": media}
        )

    return templates.TemplateResponse(
        "home.html",
        {"request": request, "products": categories}
    )


# ========= CATEGORY =========

@app.get("/category/{cat}", response_class=HTMLResponse)
def category(request: Request, cat: str, db=Depends(get_db), _: None = Depends(verify_user)):

    items = db.query(Product).filter(Product.category == cat.lower()).all()

    result = []

    for p in items:

        try:
            media = json.loads(p.media) if p.media else []
        except:
            media = []

        result.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "stock": p.stock,
            "sold": p.sold,
            "category": p.category,
            "media": media
        })

    return templates.TemplateResponse(
        "category.html",
        {"request": request, "items": result, "cat": cat.capitalize()}
    )


# ========= CART =========

@app.post("/add_to_cart")
async def add_to_cart(request: Request, item: str = Form(...), qty: int = Form(...), price: int = Form(...), image: str = Form(...)):

    username = request.cookies.get("user")
    user_cart = get_user_cart(username)

    if item in user_cart:
        user_cart[item]["qty"] += qty
    else:
        user_cart[item] = {"qty": qty, "price": price, "image": image}

    return {"message": "Added to cart"}

@app.get("/cart", response_class=HTMLResponse)
def cart_page(request: Request, _: None = Depends(verify_user)):

    username = request.cookies.get("user")
    user_cart = get_user_cart(username)

    total = sum(v["qty"] * v["price"] for v in user_cart.values())
    total_items = sum(v["qty"] for v in user_cart.values())

    return templates.TemplateResponse("cart.html",
                                      {"request": request, "cart": user_cart,
                                       "total": total, "total_items": total_items})

@app.get("/delete_cart/{item}")
def delete_cart(request: Request, item: str):

    username = request.cookies.get("user")
    user_cart = get_user_cart(username)

    user_cart.pop(item, None)

    return RedirectResponse("/cart", 302)

# ========= PAYMENT =========

@app.get("/payment", response_class=HTMLResponse)
def payment(request: Request, _: None = Depends(verify_user)):

    username = request.cookies.get("user")
    user_cart = get_user_cart(username)

    total = sum(v["qty"] * v["price"] for v in user_cart.values())
    total_items = sum(v["qty"] for v in user_cart.values())

    return templates.TemplateResponse("payment.html",
                                      {"request": request,
                                       "cart": user_cart,
                                       "total": total,
                                       "total_items": total_items})

# ========= BILL =========

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

    for name, data in items.items():
        pdf.cell(0, 8, f"{name} x {data['qty']} = Rs. {data['qty']*data['price']}", ln=True)

    pdf.cell(0, 10, f"Total Rs. {order.total}", ln=True)

    filename = f"{order.shop_name}_{order.id}.pdf".replace(" ", "_")
    path = f"static/bills/{filename}"

    pdf.output(path)
    return path

# ========= PLACE ORDER =========

@app.post("/place_order")
async def place_order(request: Request, shop_name: str = Form(...),
                      customer_name: str = Form(...),
                      phone: str = Form(...),
                      pay: str = Form(...),
                      db=Depends(get_db)):

    username = request.cookies.get("user")
    user_cart = get_user_cart(username)

    if not user_cart:
        return RedirectResponse("/cart", 302)

    for item, data in user_cart.items():
        product = db.query(Product).filter(Product.name == item).first()

        if not product or product.stock < data["qty"]:
            raise HTTPException(400, f"{item} out of stock")

    total = sum(v["qty"] * v["price"] for v in user_cart.values())

    order = Order(
        username=username,
        shop_name=shop_name,
        customer_name=customer_name,
        phone=phone,
        items=json.dumps(user_cart),
        total=total,
        payment_mode=pay,
        timestamp=datetime.now().strftime("%d-%m-%Y %H:%M")
    )

    db.add(order)

    for item, data in user_cart.items():
        p = db.query(Product).filter(Product.name == item).first()
        p.stock -= data["qty"]
        p.sold += data["qty"]

    db.commit()
    db.refresh(order)

    generate_bill(order)

    cart_store[username] = {}

    return RedirectResponse("/my_orders", 302)

# ========= ORDER HISTORY =========

@app.get("/my_orders", response_class=HTMLResponse)
def order_history(request: Request, db=Depends(get_db), _: None = Depends(verify_user)):

    username = request.cookies.get("user")

    orders_db = db.query(Order).filter(Order.username == username).all()

    orders = []
    for o in orders_db:
        orders.append({
            **o.__dict__,
            "items": json.loads(o.items)
        })

    return templates.TemplateResponse("order_history.html",
                                      {"request": request, "orders": orders})



