import os
import glob
import sys
import datetime
import numpy as np

import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

from rpdgrib.colormap import colormap as cm
from rpdgrib.rpdgrib import Rpdgrib as rgrib

DEFAULT_WIDTH = 5

data_crs = ccrs.PlateCarree()

@staticmethod
def calc_figsize(georange):
    latmin, latmax, lonmin, lonmax = georange
    ratio = (latmax - latmin) / (lonmax - lonmin)
    figsize = (DEFAULT_WIDTH, DEFAULT_WIDTH * ratio)
    return figsize

@classmethod
def sate_name(fname):
    if fname[:3] == "H2A":
        name = "HY-2A"
    elif fname[:3] == "H2B":
        name = "HY-2B"
    elif fname[:3] == "H2C":
        name = "HY-2C"
    else:
        name = "HY-2"
    return name


def grid(fname, georange, sfname):
    lats, lons, data_spd, data_dir, data_time = rgrib.extract(fname, 0)
    
    # get range
    latmin, latmax, lonmin, lonmax = georange
    
    # get an appropriate fig sizes
    figsize = calc_figsize(georange)
    
    # set figure-dpi
    dpi = 1500 / DEFAULT_WIDTH
    
    # set axes projection
    proj = ccrs.PlateCarree(central_longitude=180)
    
    # set figure and axis
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes(
        [0, 0, 1, 1], projection=proj
    )
    ax.set_extent([lonmin, lonmax, latmin, latmax], crs=data_crs)
    
    # process data's valid time (latest)
    data_time = datetime.datetime.strptime(data_time, "%Y%m%dT%H%M%S").strftime('%Y/%m/%d %H%MZ')
    
    print("...PLOTING...")
    
    '''
    # get area's max wind
    # You can delete these codes if you do not want to show the max wind
    '''
    dspd = []
    data = data_spd.filled()
    for i in range(len(lons)):
        for j in range(len(lons[i])):
            if lons[i][j] <= lonmax and lons[i][j] >= lonmin and lats[i][j] <= latmax and lats[i][j] >= latmin:
                if not data[i][j] == 1e+20:
                    dspd.append(data[i][j])
            else:
                continue
    if len(dspd) > 0:
        damax = round(max(dspd), 1)
    else:
        damax = "0.0"
    
    # add annotate at the top of figure
    text = f'{sate_name(fname)} Scatterometer Level 2B 10-meter Wind (brabs) [kt]\nValid Time: {data_time} | Max. Wind: {damax}kt'
    bbox_alpha = 0.5
    plt.annotate(
        text,
        xy=(0.012, 0.987),
        va="top",
        ha="left",
        xycoords="axes fraction",
        bbox=dict(facecolor="w", edgecolor="none", alpha=bbox_alpha),
        fontsize=6,
        family="DejaVu Sans",
        weight="500",
    )
    
    # plot brabs with colormap and color-bar
    cmap, vmin, vmax = cm.get_colormap("hy")
    ver = np.asarray([spd*np.sin(agl*np.pi/180) for spd,agl in zip(data_spd,data_dir)])
    hriz = np.asarray([spd*np.cos(agl*np.pi/180) for spd,agl in zip(data_spd,data_dir)])
    bb = ax.barbs(
        lons,
        lats,
        ver,
        hriz,
        data_spd,
        cmap=cmap,
        clim={vmax:vmax, vmin:vmin},
        pivot='middle',
        length=3.5,
        linewidth=0.5,
        transform=data_crs,
    )
    cb = plt.colorbar(
        bb,
        ax=ax,
        orientation='vertical',
        pad=0,
        aspect=48,
        fraction=0.02,
    )
    # set color-bar params
    cb.set_ticks([5, 15, 25, 35, 45, 55, 65])
    cb.ax.tick_params(labelsize=5)
    
    # add coastlines
    ax.add_feature(
        cfeature.COASTLINE.with_scale("10m"),
        facecolor="None",
        edgecolor="k",
        lw=0.5,
    )
    
    # add gridlines
    dlon = dlat = 2
    xticks = np.arange(int(lonmin - lonmin%dlon) - dlon, int(lonmax - lonmax%-dlon) + dlon, dlon)
    yticks = np.arange(int(latmin - latmin%dlat) - dlat, int(latmax - latmax%-dlat) + dlat, dlat)
    # fix labels location
    xticks = xticks[(xticks>lonmin) & (xticks<lonmax)]
    yticks = yticks[(yticks>latmin) & (yticks<latmax)]
    if xticks[-1] / lonmax > 0.98 and xticks[-1] / lonmax < 1:
        ha = 'right'
    elif xticks[0] / lonmin >= 1 and xticks[0] / lonmin < 1.02:
        ha = 'left'
    else:
        ha = 'center'
    if yticks[-1] / latmax > 0.98 and yticks[-1] / latmax < 1:
        va = 'top'
    elif yticks[0] / latmin >= 1 and yticks[0] / latmin < 1.02:
        va = 'bottom'
    else:
        va = 'center'
    # fix xticks
    xi = np.where(xticks > 180)
    for i in range(len(xi[0])):
        xticks[xi[0][i]] = xticks[xi[0][i]] - 360
    lon_formatter = LongitudeFormatter(zero_direction_label=False)
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)
    gl = ax.gridlines(
        crs=data_crs,
        draw_labels=False,
        linewidth=0.6,
        linestyle=':',
        color='k',
        xlocs=xticks,
        ylocs=yticks,
    )
    # add x/y labels
    for i in yticks:
        if i < latmin or i > latmax:
            continue
        if i > 0:
            j = str(i) + "°N"
        elif i < 0:
            j = str(-1 * i) + "°S"
        else:
            j = str(i) + "°"
        plt.text(
            transform=data_crs,
            s=j,
            x=lonmin,
            y=i,
            va=va,
            fontsize=4,
            family="DejaVu Sans",
            weight="500",
            color="#000000"
        )
    for i in xticks:
        if i > 180:
            j = str(360 - i) + "°W"
            k = i
        elif i < 180 and i > 0:
            j = str(i) + "°E"
            k = i
        elif i < 0:
            j = str(-1 * i) + "°W"
            k = 360 + i
        else:
            j = str(i) + "°"
            k = i
        if k < lonmin or k > lonmax:
            continue
        plt.text(
            transform=data_crs,
            s=j,
            x=i,
            y=latmin,
            ha=ha,
            fontsize=4,
            family="DejaVu Sans",
            weight="500",
            color="#000000"
        )
    
    plt.axis("off")
    
    # save figure
    ptext = sfname
    plt.savefig(
        ptext,
        dpi=dpi,
        bbox_inches="tight",
        pad_inches=0,
    )
    
    plt.close("all")

# Just a demonstrate code
grid("H2C/H2C_OPER_SCA_L2B_OR_20210731T015738_20210731T034357_04277_dps_250_21_owv.h5", (-40,-25,150,165), "H2C_OPER_SCA_L2B_OR_20210731T015738_20210731T034357_04277_dps_250_21_owv")