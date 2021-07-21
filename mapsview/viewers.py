import holoviews as hv
from holoviews import opts, dim, streams
import streamz.dataframe
import numpy as np
import panel as pn
import param
from itertools import tee
import matplotlib
from matplotlib import pyplot as plt
from itertools import tee
import copy
from sklearn.decomposition import NMF
hv.extension('bokeh')

# from plasview.utils import hdf2xds, get_ranges, stretch_arr, get_percentiles, get_extents
# from specview.hooks import y_bare_hook, transp_hook

from mapsview.utils.odemis_file_utils import hdf2xds, get_wavelengths1
# from plasview.utils.functions import maps
# from plasview.utils.odemis_file_utils import get_extrema

class BaseModeViewer(param.Parameterized):
    """
    Base class for generating dashboard depicting background-subtracted dynamic map
    
    acq : hdf5 group
        Typically selected from Odemis hdf5 file.
    """
    from holoviews.plotting import list_cmaps
    fullcolorlist = list_cmaps(provider='bokeh')+list_cmaps(provider = 'matplotlib')
    colorlist = [i for i in fullcolorlist if i[-4:] != '_r_r']
    color = param.Selector(objects = colorlist,default = 'gnuplot2')
    
    def __init__(self,acq,**params):
        super().__init__(**params)
        self.xds = hdf2xds(acq)
        self.img_data = self.xds.cts
        self.title = self.xds.name
        self.acq = acq
#         self.aspect_ratio = 4/3

    def bkgsub_data(self):
        """
        Returns a background subtracted xarray dataset
        
        """
        avg_bkg = (self.xds.isel(x=0, y=0) + self.xds.isel(x=-1, y=0))/2
        I_xarr_bkgsub = self.img_data-avg_bkg
        minimum = I_xarr_bkgsub.min()
        I_xarr_bkgsub = I_xarr_bkgsub-minimum
        return I_xarr_bkgsub.cts
        
    def get_bkgsub_dmap(self):
        """
        Returns a dynamic map of the background-subtracted CL images
        
        """
        ds_I_xarr_bkgsub = hv.Dataset((self.bkgsub_data()))
        img = ds_I_xarr_bkgsub.to(hv.HeatMap, ['x','y'], dynamic = True)
#         self.bkgsub_data().hvplot.heatmap('x', 'y', 'cts').opts(width = 400,height = 350,cmap = 'viridis')
        img = img.apply.opts(xlabel = 'x (microns)',ylabel = 'y (microns)',
                 colorbar = True, width = 400,height = 350,cmap = self.param.color)
        return img
    
    def view(self):
        return pn.Column(self.get_bkgsub_dmap(),pn.Column(self.param.color))
        
class ModeViewer(BaseModeViewer):
    """
    Extends functionality of BaseModeViewer to generate dynamically adjustable 
    layout dashboard and colorbar

    """
    columns = param.Selector(objects = [1,2,3,4,5,6],default = 3)
    font_Color = param.Color(default = '#FFFFFF')
    wl_band = param.Range(default = (400.0,700.0))
    increment = param.Number(default = 20)
    img_band = param.Integer(4, bounds=(1, None))
    intensity_Range = param.Range(default=(200,300))
    textX_pos = param.Number(default = 0)
    textY_pos = param.Number(default = 0)
        
    
    def __init__(self, acq,**params):
        """
        Returns CL maps with associated colorbars.
        
        The following parameters can be dynamically adjusted:
        
        - Color Scheme
        - Columns
        - Font color
        - Wavelength bandwidth
        - Wavelength increment between images
        - Image bandwidth
        - Intensity range
        - Text position
    
        """
        super().__init__(acq,**params)
        self.wl = self.bkgsub_data().coords['wl']
        wlmin = self.wl.min().astype(int).item()
        wlmax = self.wl.max().astype(int).item()
        Imin = self.bkgsub_data().min().item()
        Imax = self.bkgsub_data().max().item()

        self.param.wl_band.bounds = (wlmin,wlmax)
        self.param.intensity_Range.bounds = (Imin,Imax)
        self.param.increment.bounds = (0,wlmax-wlmin)

    @param.depends('wl_band','increment','color','columns')
    def maps(self,data_in,low_wl,up_wl,inc,band,low_intens,up_intens,cols,posX,posY):
        """
        Generates CL maps.
        Note: Future versions should try to incorporate a changing scalebar functionality.
              Currently, all scalebars must be hard coded.
        
        """
        def pairwise(iterable):
            a, b = tee(iterable)
            next(b, None)
            return zip(a,b)
        data = data_in
        aspect_ratio = 1
        wl_arr = np.arange(low_wl,up_wl+inc,inc)
        wl_arr = np.asarray(tuple(pairwise(wl_arr)))
        hv.extension('bokeh');
        img = [];
        for i in range(0,len(wl_arr)):
            plot = hv.Image(data.sel(wl=slice(wl_arr[i][0],wl_arr[i][0]+band)).mean('wl'),['x','y'])
            plot = plot.apply.opts(cmap = self.param.color,
                        xlabel = 'x(microns)',
                        ylabel = 'y(microns)',
                        xaxis = None,
                        yaxis = None,
                        colorbar = False,
                        clipping_colors = {'min':'black','max':'black'},
                        fontsize={'title': 12, 'labels': 45, 'xticks': 42, 'yticks': 42,'cticks': 42},
                        width = 400,
                        height = int(400*aspect_ratio),
                        toolbar = None
                      )
            plot = plot.redim.range(cts=(low_intens,up_intens))
            text = hv.Text(posX/100,posY/100,
                           '\u03BB = {a} nm'.format(a = int(np.mean((wl_arr[i][0],wl_arr[i][0]+band)))),
                           halign = 'left',
                           valign = 'bottom').apply.opts(color = self.param.font_Color,text_font_size='32pt')
    #         s = hv.Curve(([x[-725],x[-100]],[y[100],y[100]])).opts(color = arr[8],line_width = 5)
    #         l = hv.Text(x[-900],y[150],'{b} nm'.format(b = int(np.ceil(1/2*x[-100]-1/2*x[-725]))),halign = 'left',valign = 'bottom').opts(color = arr[8],text_font_size='16pt',)
            plot = plot*text
            img.append(plot)
        layout = hv.Layout(img).cols(cols)#.opts(title = filename[127:])
        return layout
    
    
    def layout(self):
        """
        Returns layout object created with def maps
        
        """
        l = self.maps(self.bkgsub_data(),
                      self.wl_band[0],
                      self.wl_band[1],
                      self.increment,
                      self.img_band,
                      self.intensity_Range[0],
                      self.intensity_Range[1],
                      self.columns,
                      self.textX_pos,
                      self.textY_pos
                     )
        return l

    def intens_scale(self,low_intens,up_intens):
        """
        Generates colorbar associated with layout object
        
        """
        a = np.array([[low_intens,up_intens]])
        colorbar = plt.figure(figsize=(1, 9))
        colorbar.patch.set_facecolor('white')
        # plt.title('Colorbar')
        plt.imshow(a, cmap=self.color)
        plt.gca().set_visible(False)
        colax = plt.axes([0.1, 0.2, 0.8, 0.6])
        plt.xticks(rotation = -90)
        plt.tick_params(labelsize = 16)
        plt.colorbar(orientation="vertical",cax = colax)
        plt.close()
        return colorbar
    
    def colorbar(self):
        """
        Returns colorbar object associated with def maps
        
        """
        c = pn.pane.Matplotlib(self.intens_scale(self.intensity_Range[0],
                                                 self.intensity_Range[1]),
                                      width_policy = 'fixed', 
                                      width = 150, height = 575,
                                      tight = True, align = 'end',
                                      margin = [60,10,0,20])
        return c
    
    def view(self):
        column1 = pn.panel(self.layout)
        column2 = pn.Column(self.colorbar)
        column3 = pn.Column(self.param)
        return pn.Row(column1,column2,column3,background = 'gray')
    
class PixelScan(ModeViewer):
    """
    This class is an prototype experiment that allows for selection of pixel spectra on a CL image.
    It addresses and solves the problem posed earlier in the semester of selecting pixels without confusing the program.
    - Note that all spectra are normalized from 0 to 1, so that their intensities are relative
    - This class is a prototype intended to merge with the ModeViewer class in future versions,
        with the goal of allowing users to select pixel spectra direclty from the layout.
    - Getting the y-axis to adjust according to actual counts in this code structure is not trivial
    - As of now, choosing CL images at an arbitrary wavelength is not available. 
    
    """
    
    def __init__(self,acq,**params):
        super().__init__(acq,**params)
        self.slice = self.bkgsub_data().isel(wl = 400)
        self.one_img = hv.Image(self.slice,['x','y']).opts(cmap = 'gnuplot2',width = 400,height = 300)
        self.pointer = streams.DoubleTap(x=0, y=0, source=self.one_img)
        
    def point_info(self,x,y):
        """
        Retrieves pointer information when selecting pixels
        """
        return hv.Points((x,y)).opts(color = 'red',size = 8,marker = 'square')
    
    def get_dmap(self):
        """
        Retrieves a DynamicMap of CL data and streams in the pointer object
        
        """
        return self.one_img * hv.DynamicMap(self.point_info, streams=[self.pointer])
    
    def find_nearest(self,array,value): 
        """
        Finds an array value that is closest to the specified bounds and returns its index
        """
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return idx

    def closepixels(self,x,y):
        """
        Returns closest pixels to the pointer
        
        """
        xpixelnear = self.find_nearest(self.slice.coords['x'],x)
        ypixelnear = self.find_nearest(self.slice.coords['y'],y)
        return xpixelnear,ypixelnear

    def get_dmap2(self):
        """
        Returns DynamicMap of pixel spectrum
        
        """
        def pixelspec(x,y):
            xval,yval = self.closepixels(x,y)
            data = self.bkgsub_data().isel(x = xval,y = yval)
            data = (data-min(data))/max(data)
            plot = hv.Curve(data).opts(width = 400, height = 300,ylabel = 'Normalized Counts')
            return plot
        
        dmap = hv.DynamicMap(pixelspec,streams=[self.pointer]).opts(ylim=(0,1))
        return dmap
    
    def view(self):
        return pn.Row(self.get_dmap(),self.get_dmap2(),background = 'gray')
        
    
class ModeViewerNMF(ModeViewer):
    """
    Performs NMF on the hyperspectral CL data.
    
    """
    ncomps = param.Integer(default = 5)
    def __init__(self,acq,**params):
        super().__init__(acq,**params)
        self.param.ncomps.bounds = (2,None)
    """
    Returns layout of endmembers and abundance maps
    
    """
    @param.depends('ncomps')
    def plotNMF(self,data_in,ncomp):
        def performNMF(a,b):
            Y = np.asarray(a).T
            Ydim = Y.shape
            Y_NMF = copy.deepcopy(Y)
            Y_NMF_flat=Y_NMF.reshape(np.prod(Ydim[:2]),Ydim[2])
            Y_NMF[Y_NMF<0]=0
            Y_model=NMF(b,max_iter=10000,init = 'nndsvd')
            Y_maps=Y_model.fit_transform(Y_NMF_flat).reshape(Ydim[:2]+(b,)).T
            Y_endmembers=Y_model.components_
            return Y_endmembers,Y_maps
        
        em,am = performNMF(data_in,ncomp)
        endmember_plots = [hv.Curve(em[i]).opts(title = 'Component {a}'.format(a = i),xlabel = 'Wavelength (nm)', ylabel = 'CL',
                                                          fontsize={'title': 12, 'labels': 12, 'xticks': 10, 'yticks': 10,'cticks': 18}) 
                           for i in range(0,len(em))]
        abundance_maps = [hv.Image(am[i]).apply.opts(cmap = self.param.color,
                                                   title = 'Component {a}'.format(a = i),
                                                   colorbar = True,xaxis = None,
                                                   yaxis = None,
                                                   fontsize={'title': 12, 'labels': 12, 'xticks': 12, 'yticks': 12,'cticks': 20}) 
                          for i in range(0,len(am))]
        endmember_plots_layout = hv.Layout(endmember_plots).opts(shared_axes = False)#.cols(cols)
        abundance_maps_layout = hv.Layout(abundance_maps).opts(shared_axes = False)#.cols(cols)
        return endmember_plots_layout, abundance_maps_layout
    
    def view(self):
        em,am = self.plotNMF(self.bkgsub_data(),self.ncomps)
        toggles = pn.Column(self.param.ncomps)
        return pn.Column(em,am,toggles, background = 'gray')
        
