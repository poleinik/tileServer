from flask import Flask
from flask import render_template,Response,request,redirect,url_for
from werkzeug.contrib.cache import MemcachedCache
from mongoengine import *
from mongoengine.queryset.visitor import Q
from PIL import Image
import io
import h5py
import numpy as np
import json
import math

app = Flask(__name__)

cache = MemcachedCache(['127.0.0.1:11211'])

connect('coordinates',alias='coord')

from models import Streets,Houses

def to_quadkey(level,tilex,tiley):
    '''
    Преобразование уровня приближения, номера тайла на оси х и у в идентификатор тайлов quadkey
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
@app.route("/spbmap/<int:level>/<float:lat>/<float:long>/<name>")
def render(level=None,lat=None,long=None,name=None):
    '''
    Отрисовка шаблона.
    '''
    if level==None:
        lat=59.939095
        long=30.315868
        level=11
        name="Санкт-Петербург"
    return render_template('main0.html',level=level,lat=lat,long=long,name=name)

@app.route("/tiles/<int:level>/<int:lat>/<int:long>/")
def tiles(level,lat,long):
    '''
    1.По координатам и уровню приближения расчитываются координаты первого тайла.
    2. Находятся координаты оставшихся 17 тайлов.
    3. Для каждого тайла рассчитывается quadkey и формируется путь.
    4. Поиск тайла в файле по указанному пути.
    5. Если найден, то преобразуется в байты и отправляется клиенту,
       если нет - создается однотонное изображение, отправляется клиенту.
    '''
    def stream():
        with h5py.File('tile2db.hdf5', 'r') as f:
            for y in range(0,3):
                for x in range(0,7):
                    path,quadkey=get_path(to_quadkey(level,lat+x,long+y))
                    rv = cache.get(quadkey)
                    if rv is None:
                        try:
                            img=f[path].attrs[quadkey].tobytes()
                        except:
                            newimg=Image.new('RGB',(256,256),(170,170,170))
                            img = io.BytesIO()
                            newimg.save(img, 'JPEG', quality=70)
                            img=img.getvalue()
                            cache.set(quadkey, img, timeout=5 * 60)
                    else:
                        img=rv
                    yield img
    return Response(stream(),mimetype="image/jpeg")

@app.route("/get_coord")
def get_coord():
    '''
    Получение координат улицы по ее названию.
    '''
    if request.method=='GET':
        adress=request.args.get('search')
        if adress.replace(' ','').isalpha():
            try:
                street=Streets.objects.get(name__icontains=adress)
                latitude=street.latitude
                longtitude=street.longtitude
                level=15
                name=street.name
            except KeyError:
                longtitude,latitude,level,name=None,None,None,None

        else:
            adress=adress.split()
            for slice in adress:
                if slice.isdigit():
                    number=int(slice)
                    adress.pop(adress.index(slice))
            street=' '.join(adress)
            try:
                house=Houses.objects.get(Q(street__icontains=street) & Q(number=number))
                longtitude=house.longtitude
                latitude=house.latitude
                name=house.street+' '+str(house.number)
                level=15
            except KeyError:
                longtitude,latitude,level,name=None,None,None,None


    return redirect(url_for('render',level=level,lat=latitude,long=longtitude,name=name))

if __name__ == '__main__':
    app.run()
