import sqlite3 as sql
# import aiosqlite
from fastapi import FastAPI, status, Response
from fastapi import Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

@app.on_event("startup")
async def startup():
    app.db_connection = sql.connect('chinook.db')
    # app.db_connection = await aiosqlite.connect('chinook.db')

@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()

@app.get("/") 
async def root():
    return JSONResponse(status_code=200, content={"detail": {"status": "hello"}})

async def get_db():
    factory = db_connection.row_factory
    db_connection.row_factory = sql.Row
    try:
        yield db_connection
    finally:
        db_connection.row_factory = factory

# @app.get("/data")
# async def root():
#     cursor = await app.db_connection.execute("....")
#     data = await cursor.fetchall()
#     return {"data": data}




# SELECT title, artistid FROM albums WHERE albumid = 1;

@app.get("/tracks/", status_code=200)
async def get_tracks(page:int = 0, per_page:int = 10):
    with sql.connect('chinook.db') as connection:
        connection.row_factory = sql.Row
        cursor = connection.cursor()
        offset = page * per_page
        tracks = cursor.execute(
            "SELECT trackid, name, albumid, mediatypeid, genreid, composer, milliseconds, "
            "bytes, unitprice FROM tracks ORDER BY trackid LIMIT ? OFFSET ?", (per_page, offset)
        ).fetchall()
    return tracks 

@app.get("/tracks/composers", status_code=200)
async def get_composers_tracks(composer_name:str = "AC/DC"):
    with sql.connect('chinook.db') as connection:
        # formatuje output
        connection.row_factory = lambda c, x: x[0]
        cursor = connection.cursor() 
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

class Album(BaseModel):
    title: str
    artist_id: int
 
class Odpowiedz(BaseModel):
    id: int
    album: Album

@app.post("/albums",response_model=Odpowiedz)
async def add_album(album: Album):

    with sql.connect('chinook.db') as connection:
        cursor = connection.cursor() 
        artist = cursor.execute(
        """SELECT artistid AS artist_id, name AS artist_name
         FROM artists WHERE artistid = ?""",
        (album.artist_id, )).fetchone()

    if artist:

    # INSERT INTO
    # {
    # "AlbumId": int,
    # "Title": str,
    # "ArtistId": int
    # }
        with sql.connect('chinook.db') as connection:
            cursor = connection.cursor() 
            artist = cursor.execute(
            """SELECT artistid AS artist_id, name AS artist_name
             FROM artists WHERE artistid = ?""",
            (album.artist_id, )).fetchone()

        print(f"{artist=}")
        return JSONResponse(status_code=200, content={"detail": {"ok": "test"}})
    else:
        return JSONResponse(status_code=404, content={"detail": {"error": "ArtistID not exists"}})
    return

    odpowiedz = Odpowiedz(id=app.licznik._value,patient=pt)
    app.licznik.release()
    app.pacjenci.append(odpowiedz) # dla zadania 4
    return odpowiedz



# @router.post("/albums", status_code=status.HTTP_201_CREATED, response_model=Album)
# async def new_album(album: NewAlbumRequest, db: sql.Connection = Depends(get_db)):
#     artist = db.execute(
#         "SELECT name FROM artists WHERE artistid = ?;", (album.artist_id,)
#     ).fetchone()
#     if not artist:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail={"error": {"error": f"No artist with this Id: {album.artist_id}"}},
#         )
#     cursor = db.execute(
#         "INSERT INTO albums (title, artistid) VALUES (?, ?);",
#         (album.title, album.artist_id),
#     )
#     db.commit()
#     album = db.execute(
#         "SELECT albumid, title, artistid FROM albums WHERE albumid = ?;",
#         (cursor.lastrowid,),
#     ).fetchone()
#     return album










# testy
@app.get("/patient/{pk}")
def zwrocPacjenta(pk: int):
    return {"ok":pk}

@app.get("/request_wiele_parametrow/")
def read_item(request: Request):
    print(f"{request.query_params=}")
    return request.query_params

@app.get("/dodaj_dwie_liczby/")
def read_item(i:int = 0, j:int = 0):
    print(type(i))
    return {"suma": i+j}


@app.get("/html", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <h1>Look ma! HTML!</h1>
        </body>
    </html>
    """