from scipy import optimize
import numpy
import matplotlib.pyplot as plt
import inspect

class fits:
   def __init__(self, function):
     self.function = function

#-------------------------------------------------------------------------------#
#
#  DIFFERENT TYPES OF FITS ARE DEFINED HERE
#
#-------------------------------------------------------------------------------#
# Currently accepts fits of maximum 5 parameters


#------------------- GAUSSIAN
# p0 = amplitude
# p1 = center
# p2 = 1/e^2 width
# p3 = offset
gaus1d = fits( lambda x,p0,p1,p2,p3 : p0*numpy.exp(-((x-p1)/p2)**2)+p3 )
gaus1d.fitexpr = 'a[0] * exp( - ( (x-a[1]) / a[2] )**2 )+a[3]'

#------------------- EXPONENTIAL
# p0 = start value
# p1 = decay constant
# p2 = offset
exp1d = fits( lambda x,p0,p1,p2:  p0*numpy.exp(-(x)/p1)+p2)
exp1d.fitexpr = 'a[0] * exp( - x / a[1]  )+a[2]'	

#------------------- SINE
# p0 = amplitude
# p1 = frequency
# p2 = phase
# p3 = offset
sine = fits( lambda x,p0,p1,p2,p3: p0*numpy.sin(p1*x*numpy.pi*2-p2)+p3 )
sine.fitexpr = 'a[0] * sin( a[1]*x*2*pi-a[2]) + a[3]'

#------------------- EXPONENTIAL DECAY SINE
# p0 = amplitude
# p1 = frequency
# p2 = phase
# p3 = decay constant
# p4 = offset
expsine = fits( lambda x,p0,p1,p2,p3,p4: p0*numpy.sin(p1*x*numpy.pi*2-p2)*numpy.exp(-x*p3)+p4 )
expsine.fitexpr = 'a[0]*sin( a[1]*x*2*pi-a[2] )*exp(-x*a[3]) + a[4]'

#------------------- TEMPERATURE
# p0 = initial 1/e size
# p1 = Temperature
temperature = fits( lambda x,p0,p1 : (p0**2+13.85e-6*1e8*2*p1*x**2)**0.5 )
temperature.fitexpr = '(a[0]^2+2*kb/M*a[1]*x^2)^0.5'

#------------------- LORENTZIAN
# p0 = amplitude
# p1 = center
# p2 = linewidth
# p3 = offset
lorentz1d = fits( lambda x,p0,p1,p2,p3 : p0*( 1 / ( numpy.pi * p2 * ( 1 + (( x - p1 ) / p2)**2 ) ) ) + p3 )
lorentz1d.fitexpr = ' a[0]*( 1 / ( pi * a[2] * ( 1 + (( x - a[1] ) / a[2])**2 ) ) ) + a[3] )'

#------------------- RABI RESONANCE (aka SINC)
# p0 = amplitude
# p1 = center frecuency
# p2 = pulse duration
# p3 = offset
# numpy defines sinc(x) as sin(pi*x) / (pi*x) 
# so sin(x)/x = numpy.sinc( x/pi ) 
rabiresonance = fits( lambda x,p0,p1,p2,p3: p0*(numpy.sinc( (1/numpy.pi) * 2*numpy.pi*(x-p1) * (p2 / 2.))**2. ) +p3 )
rabiresonance.fitexpr = 'a[0]*sinc^2( 2*pi * (x-a[1]) * a[2]/2 ) +a[3]'

#------------------- LINE
# p0 = slope
# p1 = intercept
linear = fits( lambda x,p0,p1: p0*x+p1 )
linear.fitexpr = 'a[0]*x + a[1]'

#------------------- GAUSSIAN BEAM 1070 nm (x in MIL, w in uMETER)
l1070 = 1070. * 25.4 / 1000.
beam1070 = fits( lambda x,p0,p1: p0*numpy.sqrt( 1 +  ( (x-p1)/(numpy.pi*p0*p0/l1070) )**2. ) )
beam1070.fitexpr = 'a[0] * sqrt ( 1 + ( (x-a[1]) / ( pi * a[0]^2 / lambda ) )**2 )'

 

fitdict = {}
fitdict['Gaussian'] = gaus1d
fitdict['Lorentzian'] = lorentz1d
fitdict['Exp'] = exp1d
fitdict['Sine'] = sine
fitdict['ExpSine'] = expsine
fitdict['Temperature'] = temperature
fitdict['RabiResonance'] = rabiresonance
fitdict['Linear'] = linear
fitdict['Beam1070'] = beam1070


#-------------------------------------------------------------------------------#
#
#  THE FITTING PROCEDURES ARE DEFINED BELOW
#
#-------------------------------------------------------------------------------#
def fit_function(p,data,function):
    # Chekck the length of p
    pLen = len(inspect.getargspec(function)[0])-1
    p0 = p[0:pLen]
   
    datax=data[:,0]
    datay=data[:,1]	   
    pfit, pvariance = optimize.curve_fit(function,datax,datay,p0)
    error=[]
    for i in range(len(pfit)):
        try:
          error.append(pvariance[i][i]**0.5)
        except:
          print "There was an error and a proper fit could not be obtained!"
          error.append( 0.00 )
    
    error = numpy.append(numpy.array(error),numpy.zeros(5-len(p0))).reshape(5,1)

    # Return same length of pfit
    pfit = numpy.append(numpy.array(pfit),numpy.zeros(5-len(p0))).reshape(5,1)
    #pfit = numpy.concatenate((pfit,numpy.zeros(5-len(p0))))
    
    return pfit,error

def plot_function(p,datax,function):
    # Chekck the length of p
    pLen = len(inspect.getargspec(function)[0])-1
    p0 = p[0:pLen]
    x = numpy.linspace(numpy.min(datax), numpy.max(datax), 200)
    y = function(x,*p0)
    return x, y

def fake_data(p,datax,function):
    # Chekck the length of p
    pLen = len(inspect.getargspec(function)[0])-1
    p0 = p[0:pLen]
    y = function(datax,*p0)
    return datax, y
    

def test_function(p,function):
	# generate random data
	ax=numpy.linspace(0,3,12)
	x,dat = fake_data( p, ax, function)
	ay = numpy.array(dat)
	noise = 200*(numpy.random.rand(ax.shape[0])-0.5)
	noisydat = ay+noise
        randomdata = numpy.transpose(numpy.array((ax,noisydat)))

	# fit noisy data, starting from a random p0
        p0 = p + p*(0.2*(numpy.random.rand(len(p))-0.5))
        print '          Fake data = ' + str(p)
        print 'Starting parameters = ' + str(p0)
	pFit , error = fit_function( p0, randomdata,function)
        print '         Fit result = ' + str(pFit)

	# Get a plot of the fit results
	fitX, fitY = plot_function(pFit, randomdata[:,0],function)
	# Show the plot on screen

	plt.plot(ax, noisydat,'.')
	plt.plot(fitX,fitY,'-')
	plt.show()

try:
  from enthought.traits.api import *
  from enthought.traits.ui.api import View, Item, Group, HGroup, VGroup, HSplit, VSplit,Handler, CheckListEditor, EnumEditor, ListStrEditor,ArrayEditor, spring
except:
  from traits.api import *
  from traitsui.api import View, Item, Group, HGroup, VGroup, HSplit, VSplit,Handler, CheckListEditor, EnumEditor, ListStrEditor,ArrayEditor, spring

import pickle

class Fits(HasTraits):
    """ Object used to do fits to the data
    """
    doplot = Bool(False, desc="plot?: Check box to plot with the current params", label="plot?")
    dofit = Bool(False, desc="do fit?: Check box to enable this fit", label="fit?")
    fitexpr = Str(label='f(x)=')
    func = Enum(fitdict.keys())
    x0 = Float(-1e15, label="x0", desc="x0 for fit range")
    xf = Float(1e15, label="xf", desc="xf for fit range")
    
    y0 = Float(-1e15, label="y0", desc="y0 for fit range")
    yf = Float(1e15, label="yf", desc="yf for fit range")

    a0 = Array(numpy.float,(5,1),editor=ArrayEditor(width=-100))
    a = Array(numpy.float,(5,1),editor=ArrayEditor(width=-100))
    ae = Array(numpy.float,(5,1),editor=ArrayEditor(width=-100))
	
    traits_view = View(
                    Group(Group(
                       Item('doplot'),
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
        try: 
          self.fitexpr = fitdict[self.func].fitexpr
        except:
          print "No fit called %s exists! Program will exit." % self.func
          exit(1)
                              
    def fit(self,data):
        fitdata, n = self.limits(data)
        if n == 0:
            print "No points in the specified range [x0:xf], [y0:yf]"
            return None,None
        f = fitdict[self.func]
        if not self.dofit:
          print "Evaluating %s" % self.func
          return plot_function(self.a0[:,0] , fitdata[:,0], f.function)
        else:
          print "Fitting %s" % self.func
          self.a, self.ae=fit_function(self.a0[:,0],fitdata,f.function)
          return plot_function(self.a[:,0] , fitdata[:,0],f.function)
           
if __name__ == "__main__":
	print ""
	print "------ Testing fitlibrary.py ------"
	print ""

	test_function([1000,700],fitdict['Temperature'].function)



    
