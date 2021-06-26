"""
Utilities that depend on hdf5 files.
"""

import numpy as np

def get_ranges(acq, mult_scale=1e6):
    """
    Get points along x and y dimensions for given acquisition.
    Parameters
    ----------
    acq : hdf5 group
        
    mult_scale : float
         (Default value = 1e6)

    Returns
    -------
    x_rng, y_rng : tuple
    """
    arr = acq['ImageData']['Image'][()].squeeze()
    ny, nx = arr.shape[-2:] # need to exlude wl dim for Acq 2
    
    yscale = acq['ImageData']['DimensionScaleY'][()]*mult_scale 
    xscale = acq['ImageData']['DimensionScaleX'][()]*mult_scale 
    yoff = acq['ImageData']['YOffset'][()]*mult_scale
    xoff = acq['ImageData']['XOffset'][()]*mult_scale
    
    ylen = ny*yscale
    xlen = nx*xscale
    x0 = -xlen/2 + xoff
    x1 = xlen/2 + xoff
    y0 = -ylen/2 + yoff
    y1 = ylen/2 + yoff
    
    x_rng = np.arange(x0+xscale/2, x1, xscale)
    y_rng = np.arange(y0+yscale/2, y1, yscale)[::-1] # for proper xarray coords
    
    return x_rng, y_rng

def hdf2xds(acq):
    """
    Converts hdf5 group into an xarray Dataset.
    Parameters
    ----------
    acq : hdf5 group

    Returns
    -------
    xarray Dataset
    """
    import xarray as xr

    arr = acq['ImageData']['Image'][()].squeeze()
    title = acq['PhysicalData']['Title'][()]
    x_rng, y_rng = get_ranges(acq)
    coords = {'x' : xr.DataArray(data=x_rng, name='x', dims=['x'], attrs={'units':'μm'}),
              'y' : xr.DataArray(data=y_rng, name='y', dims=['y'], attrs={'units':'μm'})}
   
    ds_dims = ['y','x']
#     if title == 'Spectrum':
    wl_vals = acq['ImageData']['DimensionScaleC'][()]*1e9
    coords['wl'] = xr.DataArray(data=wl_vals, name='wl', dims=['wl'], 
                attrs={'units':'nm', 'long_name':'Wavelength'})
    ds_dims.insert(0, 'wl')

    return xr.Dataset(   
            {'cts' : xr.DataArray(arr, dims=ds_dims, attrs={'long_name':'Counts'})},
            coords=coords,
            attrs = {'name':title}
            )

def get_img_arr(h5):
    return h5['ImageData']['Image'][()].squeeze()

def get_extra_settings(h5):
    import json
    dct = h5['Acquisition1']['PhysicalData']['ExtraSettings'][()][0] # is string
    dct = json.loads(dct) # convert json dict to python dict
    return dct

def get_sem_resolution(h5):
    """
    Output shape --> (res_x, _resy)
    """
    dct = get_extra_settings(h5)
    return np.array(dct['SEM E-beam']['resolution'][0])

def get_wavelengths(h5):
    return h5['Acquisition2']['ImageData']['DimensionScaleC'][()]

def get_wavelengths1(h5):
    return h5['ImageData']['DimensionScaleC'][()]



