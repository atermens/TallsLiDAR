# -----------------------------------------------------------------------------
# Name:        TallsLiDAR.py
# Purpose:     Generar arxius GeoJSON amb els talls LiDAR que escollim, a 
#              partir dels identificadors del tall 2kmx2km
#              Per exemple, pels projectes SOLAR processarem el tall 500mx500m
#
# Author:      a.termens
#
# Created:     18/09/2019
# Copyright:   (c) a.termens 2019
# Licence:     CC-BY-4.0
# Last Update: 20/04/2022
# -----------------------------------------------------------------------------
# References ...
# BBOX Tall 2km x 2km: 256000,4488000,528000,4752000
# -----------------------------------------------------------------------------
# !/usr/bin/env python

import sys
import os

import csv
import json

# -----------------------------------------------------------------------------
# ... constants ...
CRS = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25831"}}

TALL_CONFIG = {
    "2km": {"tpare":"2km", "ncols":1, "nrows":1, "dxy":2000, "factor":1000, "ip":3}, # default
    "1km": {"tpare":"2km", "ncols":2, "nrows":2, "dxy":1000, "factor":1000, "ip":3}, 
    "500m":{"tpare":"2km", "ncols":4, "nrows":4, "dxy": 500, "factor": 100, "ip":4}, 
    }


class Tall_configuration:
    def __init__(self, ktall="2km"):
        self.tall = ktall
        data = TALL_CONFIG.get(ktall, {"tpare":"none", "ncols":0, "nrows":0, "dxy":0, "factor":0, "ip":0} )
        # data es un diccionari on si no existeix ens assegurem que retorna els valors de control
        self.tpare = data["tpare"]
        self.ncols = data["ncols"]
        self.nrows = data["nrows"]
        self.dxy = data["dxy"]
        self.factor = data["factor"]
        self.ip = data["ip"] 



def LoadIdsLiDARcat():
    tconfig = Tall_configuration("2km")

    id_list = []    
    # Tall_LiDARCAT_2x2.csv has id,bloc (i.e. "1",260512.00000) tall 2km x 2km
    # id,bloc
    # "1",260512.000000000000000  >>> cantonada SW (260000.0,4512000.0)
    # "2",260514.000000000000000  >>> cantonada SW (260000.0,4514000.0)
    # ...
    with open('Tall_LiDARCAT_2x2.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        nlin = 0
        for row in csv_reader:
            if nlin > 0:
                x = int(float(row[1][:tconfig.ip]))*1000.0 # 
                y = 4000000.0 + int(float(row[1][tconfig.ip:]))*1000.0 
                id_list.append([x,y])
            nlin += 1

    return id_list



def LoadIdsLiDAR(ktall="2km"):
    tconfig = Tall_configuration(ktall)
    
    id_list = []
    for sw in LoadIdsLiDARcat():
        for cr in range(tconfig.ncols):
            x = sw[0] + cr*tconfig.dxy
            for fr in range(tconfig.nrows):
                y = sw[1] + fr*tconfig.dxy
                id_list.append([x,y])
    
    return id_list



class LiDARbloc:
    def __init__(self, x, y, ktall="2km"):
        # id es l'identificador del bloc del tall ktall on es fa referencia a les 
        # coordenades de la cantonada SW
        # x,y son els coordenades de la cantonada SW que servira per
        # identificar el bloc
        # key del tall "2km", "1km", "500m",...
        tconfig = Tall_configuration(ktall)
        ix = int(x / tconfig.factor)
        iy = int((y-4000000) / tconfig.factor)
        
        self.id = int("{}{}".format(ix,iy))
        self.SW = [x, y]
        self.NW = [x, y + tconfig.dxy]
        self.NE = [x + tconfig.dxy, y + tconfig.dxy]
        self.SE = [x + tconfig.dxy, y]
        # assignem geometria GeoJSON
        pol = [self.SW, self.NW, self.NE, self.SE, self.SW]
        self.jsgeom = {}
        self.jsgeom["type"] = "MultiPolygon"
        self.jsgeom["coordinates"] = [[pol]]



def write_LiDAR_geojson(ktall="2km"):
    bloc_data_list = []
    nb = 0
    for sw in LoadIdsLiDAR(ktall):
        nb += 1
        bloc = LiDARbloc(sw[0], sw[1], ktall)
        bloc_data = {}
        bloc_data["type"] = "Feature"
        bloc_data["properties"] = {"id": nb, "bloc": bloc.id }
        bloc_data["geometry"] =  bloc.jsgeom
        bloc_data_list.append(bloc_data)

    print(" Total de blocs a generar tall {} {} {}".format(ktall, nb, len(bloc_data_list)))

    dict = {}
    dict["type"] = "FeatureCollection"
    dict["name"] = "Tall LiDAR {}".format(ktall)
    dict["crs"] = CRS
    dict["features"] = bloc_data_list

    with open('LiDAR_{}.geojson'.format(ktall), 'w') as f:
        json.dump(dict, f, ensure_ascii=False, indent=4)
    
    return 0



        
def main(argv=None):
    ierr = 0
    for ktall in ["2km", "1km", "500m"]:
        ierr += write_LiDAR_geojson(ktall)
    return ierr


if __name__ == '__main__':
    sys.exit(main(sys.argv))
