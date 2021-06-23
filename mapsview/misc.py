class ModeViewerNMF(ModeViewer):
    ncomps = param.Integer(default = 2)
    
    def __init__(self,acq,**params):
        super().__init__(acq,**params)
        self.param.ncomps.bounds = (2,None)
    
    @param.depends('ncomps','columns')
    
    def performNMF(self,ncomp):
        Y = np.asarray(self.bkgsub_data()).T
        Ydim = Y.shape
        Y_NMF = copy.deepcopy(Y)
        Y_NMF_flat=Y_NMF.reshape(np.prod(Ydim[:2]),Ydim[2])
        Y_NMF[Y_NMF<0]=0
        Y_model=NMF(ncomp,max_iter=10000,init = 'nndsvd')
        Y_maps=Y_model.fit_transform(Y_NMF_flat).reshape(Ydim[:2]+(ncomp,)).T
        Y_endmembers=Y_model.components_
        return Y_endmembers,Y_maps
    
    def plotNMF(self,cols):
        em,am = self.performNMF(self.ncomps)
        endmember_plots = [hv.Curve(em[i]).opts(title = 'Component {a}'.format(a = i),xlabel = 'Wavelength (nm)', ylabel = 'CL',
                                                          fontsize={'title': 12, 'labels': 12, 'xticks': 10, 'yticks': 10,'cticks': 18}) 
                           for i in range(0,len(em))]
        abundance_maps = [hv.Image(am[i]).apply.opts(cmap = self.param.color,
                                                   title = 'Component {a}'.format(a = i),
                                                   colorbar = True,xaxis = None,
                                                   yaxis = None,
                                                   fontsize={'title': 12, 'labels': 12, 'xticks': 12, 'yticks': 12,'cticks': 20}) 
                          for i in range(0,len(am))]
        endmember_plots_layout = hv.Layout(endmember_plots).opts(shared_axes = False).cols(cols)
        abundance_maps_layout = hv.Layout(abundance_maps).opts(shared_axes = False).cols(cols)
        return endmember_plots_layout, abundance_maps_layout
    
    def get_NMF_plot(self):
        return self.plotNMF(self.columns)
    
    def view(self):
        # em2,am2 = self.plotNMF(self.columns)
        em2,am2 = self.get_NMF_plot()
        nmfwidgets = pn.Column(self.param.ncomps,
                               self.param.color,
                               self.param.columns)
        return pn.Column(em2,am2,nmfwidgets, background = 'gray')
    
    
    
    
    def plotNMF(self):
        em,am = self.performNMF(self.ncomps)
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