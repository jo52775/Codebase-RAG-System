from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database.database import get_db, engine, Base
from database.testModel import Post
app = FastAPI()

# Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root(db:Session = Depends(get_db)):
    print('DATABASE OBJECT: ', db)
    return {"Hello": "World?"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}