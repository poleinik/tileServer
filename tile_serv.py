from flask import Flask
from mongoengine import *
from flask import render_template,Response,request,redirect,url_for
from PIL import Image
import io
import h5py
import numpy as np
import json
import math

app = Flask(__name__)
connect('coordinates',alias='coord')

from models import Streets

def to_quadkey(level,tilex,tiley):
    '''
    Преобразование уровня приближения, широты и долготы в идентификатор тайлов quadkey
    '''
    quadkey=''
    for i in range(level):
        bufx=tilex&1
        bufy=tiley&1
        tilex=tilex>>1
        tiley=tiley>>1
        bufxy=bufy<<1
        bufxy=bufxy|bufx
        quadkey=str(bufxy)+quadkey
    return quadkey

def get_path(quadkey):
    '''
    Получение пути до тайла.
    Все тайлы хранятся в файле tile2db.hdf5.
    Путь до тайла определяется по его quadkey.
    '''
    root='12012121'
    path=root+'/'
    for value in quadkey[8:-1]:
        path=path+value+'/'
    return path,quadkey

@app.route("/spbmap")
@app.route("/spbmap/<int:level>/<float:lat>/<float:long>")
def crawler(level=None,lat=None,long=None):
    '''
    Отрисовка шаблона.
    '''
    if level is None:
        #Если функция не получила никаких параметров
        level=11
        lat=60.063834
        long=29.706302
    return render_template('main.html',level=level,lat=lat,long=long)

@app.route("/tiles/<int:level>/<float:lat>/<float:long>")
def tiles(level,lat,long):
    '''
    1.По координатам и уровню приближения расчитываются координаты первого тайла.
    2. Находятся координаты оставшихся 17 тайлов.
    3. Для каждого тайла рассчитывается quadkey и формируется путь.
    4. Поиск тайла в файле по указанному пути.
    5. Если найден, то преобразуется в байты и отправляется клиенту,
       если нет - создается однотонное изображение, отправляется клиенту.
    '''
    sinLat=np.sin(lat*np.pi/180)
    pixelX = ((long + 180) / 360) * 256 * 2**level
    pixelY = (0.5 - np.log((1 + sinLat) / (1 - sinLat)) / (4 * np.pi)) * 256 * 2**level
    tileX = int(pixelX / 256)
    tileY = int(pixelY / 256)
    def stream():
        with app.app_context():
            with h5py.File('tile2db.hdf5', 'r') as f:
                for y in range(0,3):
                    for x in range(0,7):
                        path,quadkey=get_path(to_quadkey(level,tileX+x,tileY+y))
                        try:
                            img=f[path].attrs[quadkey].tobytes()
                        except:
                            newimg=Image.new('RGB',(256,256),(190,170,170))
                            img = io.BytesIO()
                            newimg.save(img, 'JPEG', quality=70)
                            img=img.getvalue()
                        yield img
    return Response(stream(),mimetype="image/jpeg")

@app.route("/get_coord")
def get_coord():
    '''
    Получение координат улицы по ее названию.
    Нахождение координат для вернего левого угла.
    '''
    pxm=2.3887
    if request.method=='GET':
        name=request.args.get('search')
        street=Streets.objects.get(name=name)
        latitude=street.latitude+384*pxm*0.001/(40000/360)
        longtitude=street.longtitude-896*pxm/((40000/360)*math.cos(latitude*math.pi/180))*0.001
        #except:
        #    longtitude=0
        #    latitude=0
        #    error='По данному запросу ничего не найдено'

    return redirect(url_for('spbmap',level=15,lat=latitude,long=longtitude))
