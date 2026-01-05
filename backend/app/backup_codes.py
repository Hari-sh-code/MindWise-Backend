# Decorators

def add(func):
    def calculation():
        print("Inside calculation")
        a, b = func()
        print("Final Answer:", a + b)
    print("Calling calculation")
    return calculation


@add
def values():
    a = 4
    b = 5
    return a, b

values()

#Post Body Type

from fastapi import FastAPI, Body, Form, UploadFile, File
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: int
    in_stock: bool

@app.post("/json")
def receive_json(item: Item):
    return {
        'type':"JSON",
        'name':item.name,
        'price':item.price,
        'in_stock':item.in_stock
    }

@app.post("/text")
def receive_text(content: str = Body(...,media_type="text/plain")):
    return {
        "type":"Plain Text",
        "content":content
    }

@app.post("/form")
def receive_form(username: str = Form(...), password: str = Form(...)):
    return {
        "type":"Form Data",
        "username":username,
        "password":password
    }

@app.post("/upload")
def receive_upload(file: UploadFile = File(...)):
    return {
        "type":"File Upload",
        "filename":file.filename,
        "content":file.content_type
    }

#Post Body Type eg

from fastapi import FastAPI, Body, Form, UploadFile, File
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: int
    in_stock: bool

@app.post("/json")
def receive_json(item: Item):
    return {
        'type':"JSON",
        'name':item.name,
        'price':item.price,
        'in_stock':item.in_stock
    }

@app.post("/text")
def receive_text(content: str = Body(...,media_type="text/plain")):
    return {
        "type":"Plain Text",
        "content":content
    }

@app.post("/form")
def receive_form(username: str = Form(...), password: str = Form(...)):
    return {
        "type":"Form Data",
        "username":username,
        "password":password
    }

@app.post("/upload")
def receive_upload(file: UploadFile = File(...)):
    return {
        "type":"File Upload",
        "filename":file.filename,
        "content":file.content_type
    }

# REST API eg
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class User(BaseModel):
    name: str
    age: int
    interest: List[str]

class UserResponse(BaseModel):
    message: str
    user: User
    recommendations: List[str]

@app.get("/recommend")
def recommend(age: int, interest: str):
    if age <= 18:
        category = "Teen"
    elif age <= 40:
        category = "Adult"
    else:
        category = "Senior"

    interest = interest.lower()
    recommendation = []

    if interest in "music":
        recommendation.extend(["Spotify Playlist", "Concert Tickets"])
    elif interest in "sports":
        recommendation.extend(["Gym membership","Running Race"])
    else:
        recommendation.extend(["Super Bikes", "Cars"])

    return {"category": category,"interest": interest,"recommendation": recommendation}

@app.post("/users", response_model=UserResponse)
def create_user(user: User):
    first_interest = user.interest[0] if user.interest else "general"
    recommendation = []

    if first_interest in "music":
        recommendation.extend(["Headphones", "Concert Tickets"])
    elif first_interest in "sports":
        recommendation.extend(["Yoga mat","Running Race"])
    else:
        recommendation.extend(["Super cars", "Bicycle"])

    return {"message": "User profile was created successfully","user": user,"recommendations": recommendation}