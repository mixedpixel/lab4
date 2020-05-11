import sqlite3 as sql
# import aiosqlite
from fastapi import FastAPI, status, Response
from fastapi import Request, Query, Depends
from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from typing import Optional, List
from pydantic import BaseModel, Field

app = FastAPI()

@app.on_event("startup")
async def startup():
    app.db_connection = sql.connect('chinook.db')
    # app.db_connection = await aiosqlite.connect('chinook.db')

@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()

async def get_db():
    factory = app.db_connection.row_factory
    app.db_connection.row_factory = sql.Row
    try:
        yield app.db_connection
    finally:
        app.db_connection.row_factory = factory

@app.get("/") 
async def root():
    return JSONResponse(status_code=200, content={"detail": {"status": "hello"}})

@app.get("/tracks/", status_code=200)
async def get_tracks(page:int = 0, per_page:int = 10, db: sql.Connection = Depends(get_db)):
    offset = page * per_page
    cursor = db.cursor()
    tracks = cursor.execute(
        "SELECT trackid, name, albumid, mediatypeid, genreid, composer, milliseconds, "
        "bytes, unitprice FROM tracks ORDER BY trackid LIMIT ? OFFSET ?", (per_page, offset)
    ).fetchall()
    return tracks 

@app.get("/tracks/composers", status_code=200)
async def get_composers_tracks(composer_name:str = "AC/DC", db: sql.Connection = Depends(get_db)):
    db.row_factory = lambda c, x: x[0]
    cursor = db.cursor() 
    tracks = cursor.execute(
        "SELECT Name FROM tracks WHERE Composer = ? ORDER BY Name", (composer_name,)
    ).fetchall()

    if len(tracks) > 0:
        return JSONResponse(status_code=200, content=tracks)
    else:
        return JSONResponse(status_code=404, content={"detail": {"error": composer_name}})

# {
#     title: str,
#     artist_id: int
# }

class NewAlbum(BaseModel):
    title: str
    artist_id: int
 
class Album(BaseModel):
    AlbumId: int
    Title: str
    ArtistId: int

# @app.post("/albums",response_model=Odpowiedz)
@app.post("/albums", response_model=Album, status_code=201)
async def add_album(album: NewAlbum, db: sql.Connection = Depends(get_db)):

    cursor = db.cursor() 
    artist = cursor.execute(
        "SELECT name FROM artists WHERE artistid = ?", (album.artist_id, )
    ).fetchone()

    if not artist:
        return JSONResponse(
            status_code=404, 
            content={"detail": {"error": f"No artist with id: {album.artist_id}"}}
        )

    cursor = db.execute(
        "INSERT INTO albums (title, artistid) VALUES (?, ?)",
        (album.title, album.artist_id),
    )
    db.commit()
    album = db.execute(
        "SELECT albumid, title, artistid FROM albums WHERE albumid = ?", (cursor.lastrowid,),
    ).fetchone()
    return album

@app.get("/albums/{album_id}", response_model=Album)
async def get_album_by_id(album_id: int, db: sql.Connection = Depends(get_db)):
    album = db.execute(
        "SELECT albumid, title, artistid FROM albums WHERE albumid = ?", (album_id,),
    ).fetchone()
    if not album:
        return JSONResponse(
            status_code=404, 
            content={"detail": {"error": f"No album with id: {album_id}"}}
        )
    return album




# ZADANIE 4
# based on Mishioo's code

class CustomerUpdateRequest(BaseModel):
    company: str = None
    address: str = None
    city: str = None
    state: str = None
    country: str = None
    postalcode: str = None
    fax: str = None

class Customer(BaseModel):
    CustomerId: int
    FirstName: str
    LastName: str
    Company: str
    Address: str
    City: str
    State: str
    Country: str
    PostalCode: str
    Phone: str
    Fax: str
    Email: str
    SupportRepId: int

class CustomerExpense(BaseModel):
    CustomerId: int
    Email: str
    Phone: Optional[str]
    Sum: float = Field(..., alias="number")

class GenreSales(BaseModel):
    Name: str
    Sum: int = Field(..., alias="number")


@app.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: int, customer_data: CustomerUpdateRequest, db: sql.Connection = Depends(get_db),):
    customer = db.execute(
        "SELECT * FROM customers WHERE customerid = ?", (customer_id,)
    ).fetchone()
    if not customer:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, 
            content={"detail": {"error": f"No customer with id: {customer_id}"}}
        )

    '''
    If you want to receive partial updates, it's very useful to use the 
    parameter exclude_unset in Pydantic's model's .dict().'''   
    customer_data = customer_data.dict(exclude_unset=True)
    sql_update_command = (
        f"UPDATE customers SET "
        f"{', '.join(f'{key}=:{key}' for key in customer_data)} "
        f"WHERE customerid=:customerid;"
    )
    
    print(sql_update_command)
    
    db.execute(sql_update_command, dict(customerid=customer_id, **customer_data))
    db.commit()
    updated = {
        key: customer_data[key.lower()]
        for key in customer.keys()
        if key.lower() in customer_data
    }
    return dict(customer, **updated)



# ZADANIE 5 i 6
# based on Mishioo's code

def customers_sales(db):
    expences = db.execute(
        "SELECT c.customerid, c.email, c.phone, ROUND(SUM(i.total), 2) as number "
        "FROM customers c "
        "INNER JOIN invoices i "
        "ON c.customerid = i.customerid "
        "GROUP BY c.customerid "
        "ORDER BY number DESC, c.customerid"
    ).fetchall()
    return [CustomerExpense(**entry).dict(by_alias=False) for entry in expences]

def genres_sales(db):
    genres = db.execute(
        "SELECT g.name, SUM(i.quantity) AS number "
        "FROM tracks t "
        "JOIN invoice_items i ON i.trackid = t.trackid "
        "JOIN genres g ON g.genreid = t.genreid "
        "group by g.genreid "
        "ORDER BY number DESC, g.name"
    ).fetchall()
    return [GenreSales(**entry).dict(by_alias=False) for entry in genres]

SALES_FUNCTIONS = {
    "genres": genres_sales,
    "customers": customers_sales,
}

@app.get("/sales")
async def sales(category: str, db: sql.Connection = Depends(get_db)):
    try:
        return SALES_FUNCTIONS[category](db)
    except KeyError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, 
            content={"detail": {"error": f"Unknown category: {category}"}}
        )

# TEMP
# @app.get("/patient/{pk}")
# def zwrocPacjenta(pk: int):
#     return {"ok":pk}

# @app.get("/request_wiele_parametrow/")
# def read_item(request: Request):
#     print(f"{request.query_params=}")
#     return request.query_params

# @app.get("/dodaj_dwie_liczby/")
# def read_item(i:int = 0, j:int = 0):
#     print(type(i))
#     return {"suma": i+j}


# @app.get("/html", response_class=HTMLResponse)
# def home():
#     return """
#     <html>
#         <head>
#             <title>Some HTML in here</title>
#         </head>
#         <body>
#             <h1>Look ma! HTML!</h1>
#         </body>
#     </html>
#     """