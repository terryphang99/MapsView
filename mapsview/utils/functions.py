import numpy as np
from itertools import tee
import holoviews as hv

def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a,b)

def maps(data_in,low_wl,up_wl,inc,band,low_intens,up_intens):
    data = data_in
    aspect_ratio = 1
    wl_arr = np.arange(low_wl,up_wl+inc,inc)
    wl_arr = np.asarray(tuple(pairwise(wl_arr)))
    hv.extension('bokeh');
    img = [];
    for i in range(0,len(wl_arr)):
        plot = hv.Image(data.sel(wl=slice(wl_arr[i][0],wl_arr[i][0]+band)).mean('wl'))
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
        text = hv.Text(300,300,
                       '\u03BB = {a} nm'.format(a = int(np.mean((wl_arr[i][0],wl_arr[i][0]+band)))),
                       halign = 'left',
                       valign = 'bottom').apply.opts(color = self.param.color,text_font_size='32pt')
#         s = hv.Curve(([x[-725],x[-100]],[y[100],y[100]])).opts(color = arr[8],line_width = 5)
#         l = hv.Text(x[-900],y[150],'{b} nm'.format(b = int(np.ceil(1/2*x[-100]-1/2*x[-725]))),halign = 'left',valign = 'bottom').opts(color = arr[8],text_font_size='16pt',)
        plot = plot#*text#*s*l
        img.append(plot)
    layout = hv.Layout(img).apply.cols(self.param.columns)#.opts(title = filename[127:])
    return layout