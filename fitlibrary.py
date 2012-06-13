from scipy import optimize
import numpy
import matplotlib.pyplot as plt
import inspect

def gaus1d_function(x,p0,p1,p2,p3): return p0*numpy.exp(-((x-p1)/p2)**2)+p3
def exp_function(x,p0,p1,p2): return p0*numpy.exp(-(x)/p1)+p2
def sine_function(x,p0,p1,p2,p3): return p0*numpy.sin(p1*x*numpy.pi*2-p2)+p3
def expsine_function(x,p0,p1,p2,p3,p4): return p0*numpy.sin(p1*x*numpy.pi*2-p2)*numpy.exp(-x*p3)+p4
def temperature_function(x,p0,p1): return (p0**2+13.85e-6*1e8*2*p1*x**2)**0.5

def fit_function(p,data,function):
    # Chekck the length of p
    pLen = len(inspect.getargspec(function)[0])-1
    p0 = p[0:pLen]
    
    datax=data[:,0]
    datay=data[:,1]	   
    pfit, pvariance = optimize.curve_fit(function,datax,datay,p0)
    error=[]
    for i in range(len(pfit)):
        error.append(pvariance[i][i]**0.5)
    
    error = numpy.append(numpy.array(error),numpy.zeros(5-len(p0))).reshape(5,1)
    
    # Return same length of pfit
    pfit = numpy.append(pfit,numpy.zeros(5-len(p0))).reshape(5,1)
    
    return pfit,error

def plot_function(p,datax,function):

    # Chekck the length of p
    pLen = len(inspect.getargspec(function)[0])-1
    p0 = p[0:pLen]
    x = numpy.linspace(numpy.min(datax), numpy.max(datax), 100)
    y = numpy.array([function(i,*p0) for i in x])
    return x, y

def test_function(p,function):
	# generate random data
	ax=numpy.linspace(0,1000,100)
	x,dat = plot_function( p, ax, function)
	ay = numpy.array(dat)
	noise = 1*numpy.random.rand(100)-1
	noisydat = ay+noise-1
	# fit noisy data, starting from a random p0
	p0 = p + numpy.random.rand(len(p))-1
	pFit , error = fit_function( p0, numpy.transpose(numpy.array((ax,noisydat))),function)
	# Get a plot of the fit results
	fitX, fitY = plot_function(pFit,numpy.transpose(numpy.array((ax,noisydat))),function)
	# Show the plot on screen 
	plt.plot(ax, noisydat,'.')
	plt.plot(fitX,fitY,'-')
	plt.show()

from enthought.traits.api import *
from enthought.traits.ui.api import View, Item, Group, HGroup, VGroup, HSplit, VSplit,Handler, CheckListEditor, EnumEditor, ListStrEditor,ArrayEditor, spring
import pickle

class Fits(HasTraits):
    """ Object used to do fits to the data
    """
    def _pck_(self,action,fpck):
        if action == 'save':
            pickle.dump( self.dofit, fpck )
            pickle.dump( self.func, fpck )
            pickle.dump( self.x0, fpck )
            pickle.dump( self.xf, fpck )
            pickle.dump( self.y0, fpck )
            pickle.dump( self.yf, fpck )
            pickle.dump( self.a0, fpck )
            pickle.dump( self.a, fpck )

			
        if action == 'load':
            self.dofit =  pickle.load( fpck )
            self.func =  pickle.load( fpck )
            self.x0 = pickle.load( fpck )
            self.xf = pickle.load( fpck )
            self.y0 = pickle.load( fpck )
            self.yf = pickle.load( fpck )
            self.a0 = pickle.load( fpck )
            self.a = pickle.load( fpck )

			
    dofit = Bool(False, desc="do fit?: Check box to enable this fit", label="fit?")
    fitexpr = Str(label='f(x)=')
    func = Enum('Gaussian','Sine','ExpSine','Temperature','Exp')
    x0 = Float(-1e15, label="x0", desc="x0 for fit range")
    xf = Float(1e15, label="xf", desc="xf for fit range")
    
    y0 = Float(-1e15, label="y0", desc="y0 for fit range")
    yf = Float(1e15, label="yf", desc="yf for fit range")

    a0 = Array(numpy.float,(5,1),editor=ArrayEditor(width=-100))
    a = Array(numpy.float,(5,1),editor=ArrayEditor(width=-100))
    ae = Array(numpy.float,(5,1),editor=ArrayEditor(width=-100))
	
    traits_view = View(
                    Group(Group(
                       Item('dofit'),
                       Item('func'),
                        orientation='horizontal', layout='normal'), 
                        Group(
                       Item('x0'),
                       Item('xf'), 
                       orientation='horizontal', layout='normal'),
                                               Group(
                       Item('y0'),
                       Item('yf'), 
                       orientation='horizontal', layout='normal'), 
                    Group(
                       Item('fitexpr',style='readonly')),
                    Group(
                       Item('a0'),
                       Item('a'),
					   Item('ae'),
                       orientation='horizontal'),),
                       dock='vertical',
               )
               
    def limits(self, data):
        lim=[]
        for p in data:
            
            if p[0] < self.xf and p[0] > self.x0 and p[1] > self.y0 and p[1] < self.yf:
                lim.append([p[0],p[1]])
        return numpy.asarray(lim), len(lim)
        
            
    def _setfitexprs_(self):
        if self.func == 'Gaussian':
            self.fitexpr = 'a[0] * exp( - ( (x-a[1]) / a[2] )**2 )+a[3]'
        if self.func == 'Exp':
            self.fitexpr = 'a[0] * exp( - x / a[1]  )+a[2]'			
        if self.func == 'Sine':
            self.fitexpr = 'a[0] * sin( a[1]*x*2*pi-a[2]) + a[3]'
        if self.func == 'ExpSine':
            self.fitexpr = 'a[0]*sin( a[1]*x*2*pi-a[2] )*exp(-x*a[3]) + a[4]'
        if self.func == 'Temperature':
            self.fitexpr = '(a[0]^2+2*kb/M*a[1]*x^2)^0.5' 
                              
    def fit(self,data):
        fitdata, n = self.limits(data)
        if n == 0:
            print "No points in the specified range [x0:xf], [y0:yf]"
            return None,None
        if self.func == 'Gaussian':
            if not self.dofit:
                return plot_function(self.a[:,0] , fitdata[:,0],gaus1d_function)
            else:
                print "Fitting to a Gaussian"
                self.a, self.ae=fit_function(self.a0[:,0],fitdata,gaus1d_function)
                return plot_function(self.a[:,0] , fitdata[:,0],gaus1d_function)
        if self.func == 'Sine':
            if not self.dofit:
                return plot_function(self.a[:,0] , fitdata[:,0],sine_function)
            else:
                print "Fitting to a Sine"
                self.a, self.ae=fit_function(self.a0[:,0],fitdata,sine_function)
                return plot_function(self.a[:,0] , fitdata[:,0],sine_function)
        if self.func == 'ExpSine':
            if not self.dofit:
                return plot_function(self.a[:,0] , fitdata[:,0],expsine_function)
            else:
                print "Fitting to a ExpSine"
                self.a, self.ae=fit_function(self.a0[:,0],fitdata,expsine_function)
                return plot_function(self.a[:,0] , fitdata[:,0],expsine_function)
        if self.func == 'Temperature':
            if not self.dofit:
                return plot_function(self.a[:,0] , fitdata[:,0],temperature_function)
            else:
                print "Fitting to a Temperature"
                self.a, self.ae=fit_function(self.a0[:,0],fitdata,temperature_function)
                return plot_function(self.a[:,0] , fitdata[:,0],temperature_function)
        if self.func == 'Exp':
            if not self.dofit:
                return plot_function(self.a[:,0] , fitdata[:,0],exp_function)
            else:
                print "Fitting to a Exp"
                self.a, self.ae=fit_function(self.a0[:,0],fitdata,exp_function)
                return plot_function(self.a[:,0] , fitdata[:,0],exp_function)				
	
if __name__ == "__main__":
	print ""
	print "------ Testing fitlibrary.py ------"
	print ""

	test_function([100,1e7],temperature_function)



    
