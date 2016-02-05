from scipy import optimize
import numpy
#mport matplotlib.pyplot as plt
#import inspect
import pprint

class fits:
    def __init__(self, function):
        self.function = function
        self.fitexpr = None

def fill_expr(expr, para):
    para = para.split('\n')[1:]
    for i in range(6):
        try:
            p = para[i].split('\t')
            expr = expr.replace("a[{0}]".format(i), "({0} +/- {1})".format(p[0],p[1]))
        except:
            pass
    return expr



#-------------------------------------------------------------------------------#
#
#  DIFFERENT TYPES OF FITS ARE DEFINED HERE
#
#-------------------------------------------------------------------------------#
# Currently accepts fits of maximum 5 parameters

import pandas as pd


fitdict = {}

#---------------------- GAUSSIAN
# p0 = amplitude
# p1 = center
# p2 = 1/e radius
# p3 = offset
gaus1d = fits( lambda x,p : p[0]*numpy.exp(-((x-p[1])/p[2])**2)+p[3] )
#gaus1d = fits( lambda x,p0,p1,p2,p3 : p0*numpy.exp(-((x-p1)/p2)**2)+p3 )
gaus1d.fitexpr = 'a[0] * exp( - ( (x-a[1]) / a[2] )**2 )+a[3]'
fitdict['Gaussian'] = gaus1d

#---------------------- GAUSSIAN WITHOUT OFFSET
# p0 = amplitude
# p1 = center
# p2 = 1/e width
gaus1d_no_offset = fits( lambda x,p : p[0]*numpy.exp(-((x-p[1])/p[2])**2) )
#gaus1d_no_offset = fits( lambda x,p0,p1,p2,p3 : p0*numpy.exp(-((x-p1)/p2)**2) )
gaus1d_no_offset.fitexpr = 'a[0] * exp( - ( (x-a[1]) / a[2] )**2 )'
fitdict['GaussianNoOffset'] = gaus1d_no_offset

#---------------------- EXPONENTIAL
# p0 = start value
# p1 = decay constant
# p2 = offset
exp1d = fits( lambda x,p:  p[0]*numpy.exp(-(x)/p[1])+p[2])
#exp1d = fits( lambda x,p0,p1,p2:  p0*numpy.exp(-(x)/p1)+p2)
exp1d.fitexpr = 'a[0] * exp( - x / a[1]  )+a[2]'	
fitdict['Exp'] = exp1d

#---------------------- DOUBLE EXPONENTIAL
# p0 = start value
# p1 = decay constant 1 
# p2 = offset
# p3 = kink
# p4 = decay constant 2 
exp2tau = fits( lambda x,p: numpy.piecewise( x, \
                 [x < p[3], x>= p[3] ], \
                 [ lambda x: p[0]*numpy.exp( -x/p[1]) + p[2], 
                   lambda x: (p[0]*numpy.exp( -p[3]/p[1]) + p[2])*numpy.exp( -(x-p[3])/p[4]) ] ))
exp2tau.fitexpr = 'p[0]=ampl, p[2]=offs, p[1]=tau1, p[3]=kink, p[4]=tau2'	
fitdict['DoubleExp'] = exp2tau

#---------------------- SINE
# p0 = amplitude
# p1 = frequency
# p2 = phase
# p3 = offset
#sine = fits( lambda x,p0,p1,p2,p3: p0*numpy.sin(p1*x*numpy.pi*2-p2)+p3 )
sine = fits( lambda x,p: p[0]*numpy.sin(p[1]*x*numpy.pi*2-p[2])+p[3] )
sine.fitexpr = 'a[0] * sin( a[1]*x*2*pi-a[2]) + a[3]'
fitdict['Sine'] = sine

#---------------------- EXPONENTIAL DECAY SINE
# p0 = amplitude
# p1 = frequency
# p2 = phase
# p3 = decay constant
# p4 = offset
expsine = fits( lambda x,p: p[0]*numpy.sin(p[1]*x*numpy.pi*2-p[2])*numpy.exp(-x*p[3])+p[4] )
#expsine = fits( lambda x,p0,p1,p2,p3,p4: p0*numpy.sin(p1*x*numpy.pi*2-p2)*numpy.exp(-x*p3)+p4 )
expsine.fitexpr = 'a[0]*sin( a[1]*x*2*pi-a[2] )*exp(-x*a[3]) + a[4]'
fitdict['ExpSine'] = expsine

#---------------------- EXPONENTIAL DECAY SINE PLUS LINEAR DECAY
# p0 = amplitude
# p1 = frequency
# p2 = phase
# p3 = decay constant
# p4 = offset
# p5 = slope
expsineplusline = fits( lambda x,p: p[0]*numpy.sin(p[1]*x*numpy.pi*2-p[2])*numpy.exp(-x*p[3])+p[4]+p[5]*x )
expsine.fitexpr = 'a[0]*sin( a[1]*x*2*pi-a[2] )*exp(-x*a[3]) + a[4] + a[5]*x'
fitdict['ExpSinePlusLine'] = expsineplusline

#---------------------- TEMPERATURE
#  x = time of flight
# p0 = initial 1/e size in um
# p1 = Temperature in uK
#temperature = fits( lambda x,p0,p1 : numpy.sqrt(p0**2 + 2 * 13.85e-6*1e8 * p1 * x**2 ) )
temperature = fits( lambda x,p : numpy.sqrt( p[0]**2 + 2 * 13.85e-6*1e8 * p[1] * x**2 ) )
temperature.fitexpr = '(a[0]^2+2*kb/M*a[1]*x^2)^0.5'
fitdict['Temperature'] = temperature

#---------------------- LORENTZIAN
# p0 = amplitude
# p1 = center
# p2 = linewidth
# p3 = offset
lorentz1d = fits( lambda x,p : p[0]*( 1 / ( numpy.pi * p[2] * ( 1 + (( x - p[1] ) / p[2])**2 ) ) ) + p[3] )
#lorentz1d = fits( lambda x,p0,p1,p2,p3 : p0*( 1 / ( numpy.pi * p2 * ( 1 + (( x - p1 ) / p2)**2 ) ) ) + p3 )
lorentz1d.fitexpr = ' a[0]*( 1 / ( pi * a[2] * ( 1 + (( x - a[1] ) / a[2])**2 ) ) ) + a[3] )'
fitdict['Lorentzian'] = lorentz1d

#---------------------- DOUBLE LORENTZIAN
# p0 = amplitude
# p1 = center
# p2 = linewidth
# p3 = offset
lorentzdouble = fits( lambda x,p : p[0]*( 1 / ( numpy.pi * p[2] * ( 1 + (( x - p[1] ) / p[2])**2 ) ) ) + p[3] + p[0]*( 1 / ( numpy.pi * p[2] * ( 1 + (( x - p[4] ) / p[2])**2 ) ) ))
lorentzdouble.fitexpr = ' a[0]*( 1 / ( pi * a[2] * ( 1 + (( x - a[1] ) / a[2])**2 ) ) ) + a[3] + a[0]*( 1 / ( pi * a[2] * ( 1 + (( x - a[4] ) / a[2])**2 ) ) )'
fitdict['DoubleLorentzian'] = lorentzdouble

#---------------------- RABI RESONANCE (aka SINC)
# p0 = amplitude
# p1 = center frecuency
# p2 = pulse duration
# p3 = offset
# numpy defines sinc(x) as sin(pi*x) / (pi*x) 
# so sin(x)/x = numpy.sinc( x/pi ) 
rabiresonance = fits( lambda x,p: p[0]*(numpy.sinc( (1/numpy.pi) * 2*numpy.pi*(x-p[1]) * (p[2] / 2.))**2. ) +p[3] )
#rabiresonance = fits( lambda x,p0,p1,p2,p3: p0*(numpy.sinc( (1/numpy.pi) * 2*numpy.pi*(x-p1) * (p2 / 2.))**2. ) +p3 )
rabiresonance.fitexpr = 'a[0]*sinc^2( 2*pi * (x-a[1]) * a[2]/2 ) +a[3]'
fitdict['RabiResonance'] = rabiresonance

#---------------------- LINE
# p0 = slope
# p1 = intercept
linear = fits( lambda x,p: p[0]*x+p[1] )
#linear = fits( lambda x,p0,p1: p0*x+p1 )
linear.fitexpr = 'a[0]*x + a[1]'
fitdict['Linear'] = linear

#---------------------- Dual LINE
# p0 = slope
# p1 = slope2
# p2 = kink
# p3 = offset
dlinearFunc =  lambda x,p: p[0]*x+p[3]  if x<p[2] else p[0]*p[2]+p[3]+p[1]*(x-p[2])
def dlinearF (x,p):
  y = []
  for i,j in enumerate(x):
    y.append(dlinearFunc(j,p))
  return numpy.array(y)
dlinear = fits(dlinearF)
dlinear.function = numpy.vectorize(dlinear.function)
linear = fits( lambda x,p0,p1: p0*x+p1 )
dlinear.fitexpr = 'a[0]*x + a[3] if x<a[2] else a[0]*a[2]+a[1]*(x-a[2])+a[3]'
fitdict['DLinear'] = dlinear


#---------------------- SLOPE
# p0 = slope
slope = fits( lambda x,p: p[0]*x )
slope.fitexpr = 'a[0]*x'
fitdict['Slope'] = slope

#---------------------- PARABOLA
# p0 = curvature
# p1 = center
# p2 = offset
parabola = fits( lambda x,p:  p[0] * (x-p[1])**2 + p[2]   )
parabola.fitexpr = 'p[0]*(x-p[1])**2 + p[2]'
fitdict['Parabola'] = parabola

#---------------------- SQRT
# p0 = scale
# p1 = center
# p2 = offset
squareroot = fits( lambda x,p:  p[0] * numpy.sqrt( numpy.abs(x-p[1]) ) + p[2]   )
squareroot.fitexpr = 'p[0]*sqrt(x-p[1]) + p[2]'
fitdict['Sqrt'] = squareroot

#---------------------- POWER LAW
# p0 = scale
# p1 = center
# p2 = offset
# p3 = power
powerlaw = fits( lambda x,p:  p[0] * (x-p[1])**(p[3]) + p[2]   )
powerlaw.fitexpr = 'p[0]*(x-p[1])**p[3] + p[2]'
fitdict['PowerLaw'] = powerlaw

#---------------------- GAUSSIAN BEAM 1070 nm with M^2 (x in MIL, w in uMETER)
# p0 = w0
# p1 = x0
# p2 = m2
l1070 = 1070. * 25.4 / 1000.
beam2_1070 = fits( lambda x,p: p[0]*numpy.sqrt( 1 +  ( (x-p[1])/(numpy.pi*p[0]*p[0]/l1070/p[2]) )**2. ) )
#beam1070 = fits( lambda x,p0,p1: p0*numpy.sqrt( 1 +  ( (x-p1)/(numpy.pi*p0*p0/l1070) )**2. ) )
beam2_1070.fitexpr = 'a[0] * sqrt ( 1 + ( (x-a[1]) / ( pi * a[0]^2 / lambda / a[2]) )**2 )'
fitdict['Beam1070m2'] = beam2_1070

#---------------------- GAUSSIAN BEAM 1064 nm with M^2 (x in m, w in m)
# p0 = w0
# p1 = x0
# p2 = m2
l1064 = 1064.e-9
beam2_1064 = fits( lambda x,p: p[0]*numpy.sqrt( 1 +  ( (x-p[1])/(numpy.pi*p[0]*p[0]/l1064) )**2. ) )
#beam1070 = fits( lambda x,p0,p1: p0*numpy.sqrt( 1 +  ( (x-p1)/(numpy.pi*p0*p0/l1070) )**2. ) )
beam2_1064.fitexpr = 'a[0] * sqrt ( 1 + ( (x-a[1]) / ( pi * a[0]^2 / lambda) )**2 )'
fitdict['Beam1064'] = beam2_1064

#---------------------- GAUSSIAN BEAM 1070 nm (x in MIL, w in uMETER)
# p0 = w0
# p1 = x0
l1070 = 1070. * 25.4 / 1000.
beam1070 = fits( lambda x,p: p[0]*numpy.sqrt( 1 +  ( (x-p[1])/(numpy.pi*p[0]*p[0]/l1070) )**2. ) )
#beam1070 = fits( lambda x,p0,p1: p0*numpy.sqrt( 1 +  ( (x-p1)/(numpy.pi*p0*p0/l1070) )**2. ) )
beam1070.fitexpr = 'a[0] * sqrt ( 1 + ( (x-a[1]) / ( pi * a[0]^2 / lambda ) )**2 )'
fitdict['Beam1070'] = beam1070

#---------------------- GAUSSIAN BEAM 671 nm (x in MIL, w in uMETER)
# p0 = w0
# p1 = x0
l671 = 671. * 25.4 / 1000.
beam671 = fits( lambda x,p: p[0]*numpy.sqrt( 1 +  ( (x-p[1])/(numpy.pi*p[0]*p[0]/l671) )**2. ) )
#beam671 = fits( lambda x,p0,p1: p0*numpy.sqrt( 1 +  ( (x-p1)/(numpy.pi*p0*p0/l671) )**2. ) )
beam671.fitexpr = 'a[0] * sqrt ( 1 + ( (x-a[1]) / ( pi * a[0]^2 / lambda ) )**2 )'
fitdict['Beam671'] = beam671

#---------------------- DEBYE-WALLER FACTOR
#  x = lattice depth
# p0 = amplitude
# p1 = can be interpreted as lattice depth scaling or 
#      harmonic oscillator length scaling
debyewaller = fits( lambda x,p: p[0] * numpy.exp( - 1./2. * p[1]**2 / numpy.sqrt(x) )) 
#debyewaller = fits( lambda x,p0,p1: p0 * numpy.exp( - 1./2. * p1**2 / numpy.sqrt(x) )) 
debyewaller.fitexpr = 'a[0] * exp( -1/2 * a[1]^2 / sqrt(x) )'
fitdict['DebyeWaller'] = debyewaller

#---------------------- STEP WITH SLOPE
#  x = anything
# p0 = left kink
# p1 = right kink
# p2 = left value
# p3 = right value
stepwithslope = fits( lambda x,p: numpy.piecewise( x, \
                 [x < p[0], numpy.logical_and( x>=p[0], x<p[1] ), x>=p[1]], \
                 [p[2], lambda x: p[2] + (x-p[0])*(p[3]-p[2])/(p[1]-p[0]), p[3] ]  ))  
stepwithslope.fitexpr = ' p[2] if x < p[0] ; p[3] if x > p[1] '
fitdict['StepWithSlope'] = stepwithslope


#-------------------------------------------------------------------------------#
#
#  THE FITTING PROCEDURES ARE DEFINED BELOW
#
#-------------------------------------------------------------------------------#
def mask_function( p, mask, function):

        mask = numpy.array(mask)
        p = numpy.array(p)
        mask_matrix = []
        counter = 0

        for i ,m in enumerate(mask):
                if m == 0:
                        mask_matrix.append([ 0 for j in range(mask.sum())])
                elif m ==1 :
                        mask_matrix.append([ 1 if counter==j else 0 for j in range(mask.sum())])
                        counter = counter +1

        mask_matrix = numpy.transpose(numpy.matrix(mask_matrix))
        function_masked = lambda x_m,p_m : function (x_m,(numpy.array(p_m)*mask_matrix+(1-mask)*p).tolist()[0])

        return function_masked,mask_matrix

def fit_mask_function(p,data,mask,function):

	mask = numpy.array(mask)
	p = numpy.array(p)
	mask_fun, mask_matrix = mask_function(p,mask,function)
	pfit,fiterror = fit_function((numpy.array(p)*mask_matrix.transpose()).tolist()[0],data,mask_fun)
	#print numpy.array(p)*mask_matrix.transpose(),numpy.array(pfit).reshape(1,len(pfit)),mask_matrix,mask,p
	pfit_unmask = numpy.array(pfit.reshape(1,len(pfit))*mask_matrix + (1-mask)*p)
	fiterror_unmask = numpy.array(fiterror.reshape(1,len(pfit))*mask_matrix)
        
	return pfit_unmask.reshape(5,1), fiterror_unmask.reshape(5,1)

def fit_function(p,data,function,**kwargs):
    # Chekck the length of p
    #pLen = len(inspect.getargspec(function)[0])-1
    #p0 = p[0:pLen]
    p0 = p
   
    datax=data[:,0]
    datay=data[:,1]	 

    errfunc = lambda p, x, y: function(x,p) - y
    pfit, pcov, infodict, errmsg, success = optimize.leastsq( errfunc, p0, args=(datax, datay), full_output=1)
    #pfit, pvariance = optimize.curve_fit(function,datax,datay,[p0])

   
    # Estimate the confidence interval of the fitted parameter using
    # the bootstrap Monte-Carlo method
    # http://phe.rockefeller.edu/LogletLab/whitepaper/node17.html
    residuals = errfunc( pfit, datax, datay)
    s_res = numpy.std(residuals)
    ps = []
    dataerrors = kwargs.get('dataerrors', None)
    for i in range(100):
      if dataerrors is None:
          randomdataY = datay+numpy.random.normal(0., s_res, len(datay))
      else:
          random =  numpy.array( [ numpy.random.normal(0., derr,1)[0] \
                         for derr in dataerrors ] ) 
          randomdataY = datay + random
      randomfit, randomcov = optimize.leastsq( errfunc, p0, args=(datax, randomdataY), full_output=0)
      ps.append( randomfit ) 
    ps = numpy.array(ps)
    mean_pfit = numpy.mean(ps,0)
    err_pfit = kwargs.get('nsigmas',2) * numpy.std(ps,0) # 2sigma confidence interval is used = 95.44 %
                               # 1sigma is only 68.3 %

    
    # Below is the old estimation of the fit parameter errors
    # This uses the covariance, the code was copied from the
    # scipy implementation of optimize.curve_fit
    # https://github.com/scipy/scipy/blob/master/scipy/optimize/minpack.py#L247
    if (len(datay) > len(p0)) and pcov is not None:
        s_sq = errfunc(pfit,datax,datay).sum()/(len(datay)-len(p0))
        pcov = pcov * s_sq
    else:
        pcov = numpy.inf
    error=[]
    for i in range(len(pfit)):
        try:
          error.append( numpy.absolute(pcov[i][i])**0.5)
        except:
          #print "A proper fit error could not be obtained!"
          #print "pfit = ", pfit
          #print "pcov = ", pcov
          error.append( 0.00 )
    
    # By default the bootstrap estimation is used for confidence intervals
    pfit = mean_pfit.tolist()
    error = err_pfit.tolist()

    # Was trying to return same length of pfit, take out by Ernie 08/20/12 
    pfit = numpy.array(pfit)  #numpy.append(numpy.array(pfit),numpy.zeros(5-len(p0))).reshape(5,1)
    error = numpy.array(error)#numpy.append(numpy.array(error),numpy.zeros(5-len(p0))).reshape(5,1)
    
    return pfit,error

def plot_function(p,datax,function, xlim = None, xpts=500):
    p0 = p
    
    if xlim == None: 
      x = numpy.linspace(numpy.min(datax), numpy.max(datax), xpts)
    else: 
      x = numpy.linspace(xlim[0], xlim[1], 200)
    y = function(x,p0)
    return x, y


def fake_data(p,datax,function):
    y = function(datax,p)
    return datax, y
    

def test_function(p,function):
	# generate random data
	ax=numpy.linspace(0,3,12)
	# print p
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



name= []
exper = []
for key, val in fitdict.iteritems():
    name.append(key)
    exper.append(val.fitexpr)

help_table = pd.Series(exper, index=name)





    
