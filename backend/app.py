from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import sqlite3
import time
import jwt

SECRET = "supersecret"

app = FastAPI()

# Разрешаем фронтенду обращаться к backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------
# Database helper
# ----------------------
def db():
    conn = sqlite3.connect("db.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------
# JWT helpers
# ----------------------
def create_token(user_id):
    return jwt.encode({"user_id": user_id, "exp": time.time() + 999999}, SECRET, algorithm="HS256")

def get_user_id_from_token(token):
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])["user_id"]
    except:
        raise HTTPException(401, "Invalid token")

# ----------------------
# Models
# ----------------------
class RegisterModel(BaseModel):
    username: str
    password: str

# ----------------------
# Initialize DB
# ----------------------
conn = db()
conn.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);""")
conn.execute("""CREATE TABLE IF NOT EXISTS friends(
    user_id INTEGER,
    friend_id INTEGER
);""")
conn.execute("""CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    text TEXT,
    ts INTEGER
);""")
conn.commit()

# ----------------------
# Test root endpoint
# ----------------------
@app.get("/")
async def root():
    return {"message": "Backend работает!"}

# ----------------------
# Auth endpoints
# ----------------------
@app.post("/register")
def register(body: RegisterModel):
    conn = db()
    try:
        conn.execute("INSERT INTO users(username,password) VALUES(?,?)",
                     (body.username, body.password))
        conn.commit()
        return {"ok": True}
    except:
        raise HTTPException(400, "User exists")

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE username=? AND password=?",
                        (form.username, form.password)).fetchone()
    if not user:
        raise HTTPException(401, "Invalid login")
    token = create_token(user["id"])
    return {"access_token": token, "token_type": "bearer", "user_id": user["id"]}

# ----------------------
# Friends endpoints
# ----------------------
@app.post("/add_friend/{friend_id}")
def add_friend(friend_id: int, token: str = Body(...)):
    user_id = get_user_id_from_token(token)
    conn = db()
    conn.execute("INSERT INTO friends(user_id, friend_id) VALUES(?,?)",
                 (user_id, friend_id))
    conn.commit()
    return {"ok": True}

@app.get("/users")
def get_users():
    conn = db()
    return [dict(x) for x in conn.execute("SELECT id, username FROM users").fetchall()]

@app.get("/friends")
def get_friends(token: str):
    user_id = get_user_id_from_token(token)
    conn = db()
    return [dict(x) for x in conn.execute("""
        SELECT users.id, users.username 
        FROM friends 
        JOIN users ON users.id = friends.friend_id 
        WHERE friends.user_id=?
    """, (user_id,)).fetchall()]

# ----------------------
# Messages REST
# ----------------------
@app.get("/messages/{user2}")
def get_messages(user2: int, token: str):
    user1 = get_user_id_from_token(token)
    conn = db()
    msgs = conn.execute("""
        SELECT * FROM messages 
        WHERE (sender_id=? AND receiver_id=?) 
           OR (sender_id=? AND receiver_id=?)
        ORDER BY id
    """, (user1, user2, user2, user1)).fetchall()
    return [dict(m) for m in msgs]

# ----------------------
# WebSocket chat
# ----------------------
connections = {}  # user_id -> websocket

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    token = await ws.receive_text()  # получаем JWT
    user_id = get_user_id_from_token(token)
    connections[user_id] = ws
    try:
        while True:
            data = await ws.receive_json()
            receiver = data["receiver"]
            text = data["text"]
            # сохраняем в БД
            conn = db()
            conn.execute(
                "INSERT INTO messages(sender_id,receiver_id,text,ts) VALUES(?,?,?,?)",
                (user_id, receiver, text, int(time.time()))
            )
            conn.commit()
            # отправляем получателю, если он онлайн
            if receiver in connections:
                await connections[receiver].send_json({
                    "sender": user_id,
                    "text": text
                })
    except WebSocketDisconnect:
        del connections[user_id]
