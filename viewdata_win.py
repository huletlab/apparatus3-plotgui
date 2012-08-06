from threading import Thread
from time import sleep
from enthought.traits.api import *
from enthought.traits.ui.api import View, Item, Group, HGroup, VGroup, HSplit, VSplit,Handler, CheckListEditor, EnumEditor, ListStrEditor,ArrayEditor, spring, ListEditor
from enthought.traits.ui.menu import NoButtons
from enthought.traits.ui.file_dialog import save_file,open_file
from enthought.chaco.api import Plot, ArrayPlotData
from enthought.enable.component_editor import ComponentEditor
from enthought.chaco.chaco_plot_editor import ChacoPlotItem
from mpl_figure_editor import MPLFigureEditor
from matplotlib.figure import Figure
from scipy import stats 
from numpy import loadtxt, linspace, sin
import wx
from random import choice
from configobj import ConfigObj

from qrange import qrange

import numpy
import matplotlib
import copy
import pickle
from configobj import ConfigObj

from fitlibrary import Fits

global colors 
colors = ['#0D8800','#1729E0','#00A779','#D8005F','green','red','magenta','black']

#-------------------------------------------------------------------------------#
#
#  HELPER FUNCTIONS
#
#-------------------------------------------------------------------------------#

import os
import plotconf
import datetime 
plotconfini, plotgui_path, mainpck, load_pck, use_date =  plotconf.initplotgui()
conf = ConfigObj(plotconfini)
print "Using INI file %s" % plotconfini
print "Plotgui base path is %s" % plotgui_path
print "Main pck file path is %s" % mainpck

# The correct paths are stored in the plotconfini.INI file
def LastAnalyzed():
    LASTNUM = conf['DIRECTORIES']['lastnum']
    path_is_relative = LASTNUM[0] != '/' and not ':' in LASTNUM  #works for Win and Linux
    if path_is_relative:
      LASTNUM = plotgui_path + '/' + LASTNUM
    file = open( LASTNUM,'r')
    lastnum = int( file.readline() )
    file.close()
    return lastnum

def DataDir():
    DATADIR = conf['DIRECTORIES']['datadir']
    path_is_relative = DATADIR[0] != '/' and not ':' in DATADIR  #Works for Win and Linux
    if path_is_relative: 
      DATADIR = os.path.join(plotgui_path, DATADIR)
    if use_date:
      today = datetime.date.today()
      date_path = today.strftime('%Y/%y%m/%y%m%d')
      DATADIR  = os.path.join( DATADIR, date_path )
    return DATADIR

#-------------------------------------------------------------------------------#
#
#  DATA SET
#
#-------------------------------------------------------------------------------#

class DataSet(HasTraits):
    """ Object that holds the information defining a data set"""
    def _setfitexprs_(self):
        self.fit1._setfitexprs_()

    # Data set tab
    name = Str
    plotme = Bool(False, label="plot me ?")
    X2 = Bool(False, label="X2?")
    Y2 = Bool(False, label="Y2?")
    X = Str('TRAPFREQ:modfreq', label="X")
    Y = Str('CPP:ax0w', label="Y")
    c = Str('', label="Color") 
    datadir = Str( DataDir(), label="DataDir", desc="directory where reports are located")
    range = Str( '', label="Range", desc="range of data to be plotted")
    fit1 = Instance(Fits, ())
    
    # Raw data tab
    raw_data = String()
    saveraw = Button('Save Raw Data')
    loadscan = Button('Load Scan')
  
    # Stats tab
    stat = String()

    fitw=550
    view = View( Group(
                Group(Item('plotme'),
                      Item('X2'),
                      Item('Y2'),
                      spring,
                      Item('loadscan', show_label=False ),
                      orientation='horizontal'
                      ),
    
                Item('datadir'),
                Item('range'),
                Item('c'),
                Group(
                      Item('X',show_label=True),
                      Item('Y',show_label=True),
                      label="SECTION:KEY's",
                     ),
                Group(
                      Item('fit1', style='custom', width=fitw, show_label=False),
                      show_border = True
                     ) ,label='Set'   ),
                            
                    Group(     Item (
                                    'raw_data',show_label=False, springy=True, style='custom' 
                                   ),
                               Item('saveraw',show_label=False),label='Raw Data'),
                    Group(     Item (
                                    'stat',show_label=False, springy=True, style='custom' 
                                   ),
                               label='Stats')
                                   ,dock='tab', height=600
              )

    def getdata_(self):
       """ Executes qrange to extract data from reports. 
       """
       data, errmsg, rawdat = qrange(self.datadir, self.range, self.X + " " + self.Y)
       print errmsg + '\n'
       self.raw_data = rawdat
       colnames = rawdat.split('\n')[0]
       colnames = colnames[1:].split('\t')[1:]
       s = ''
       for i in range(data.shape[1]):
         col = data[:,i]
         s00 = numpy.mean( col ) #mean 
         s01 = stats.sem( col ) #standard error of the mean 
         s02 = numpy.std( col ) #standard deviation
         s03 = numpy.max( col ) - numpy.min( col ) # peak to peak value
         s = s + colnames[i] + ':\n'
         s = s + "Mean                   = %10.6f\n" %  s00
         s = s + "Std. error of the mean = %10.6f\n" %  s01
         s = s + "Std. deviation         = %10.6f\n" %  s02
         s = s + "Pk-Pk                  = %10.6f\n" %  s03
         s = s + '\n'
       self.stat = s
       return data


    def _saveraw_changed(self):
        """ Save raw data to choosen location"""
      
        file_name = save_file()
        if file_name != '':
            file_raw=open(file_name,"w+b")
            file_raw.write('#dir:'+self.datadir+'\n')
            file_raw.write('#range:'+self.range+'\n')
            file_raw.write(self.raw_data)
            file_raw.close()
    def _loadscan_changed ( self ):
        """ Handles the user clicking the 'Loadscan...' button. Load the sweep config file
        """
        INFO = conf['DIRECTORIES']['infofile']
        infofile = open(INFO,'r')
        self.datadir =  infofile.readline()
        self.range = infofile.readline()
        self.X = infofile.readline()
        self.Y = infofile.readline()

#-------------------------------------------------------------------------------#
#
#  PROCESSING THREAD
#
#-------------------------------------------------------------------------------#

class ProcessThread(Thread):
    """ Fitting loop. This is the worker thread that retrieves the 
    data from the reports, and performs the fits. 
    """
    wants_abort = False
    autoplot = False

    def process(self, dataset_array, image_clear, figure):
        """ Spawns the processing job. """
        try:
            if self.processing_job.isAlive():
                print "Processing too slow" + '\n'
                return
        except AttributeError:
            pass
        self.processing_job = Thread(target=process, args=(dataset_array, image_clear, figure))
        self.processing_job.start()

    def run(self):
        """ Runs the plotting loop. """
        i=0
        while not self.wants_abort:
            self.process(self.datasets, self.image_clear, self.figure)
            if i==0:
                self.wants_abort = not self.autoplot
            if i>0 and not self.wants_abort: 
                p0= LastAnalyzed()
                while p0 == LastAnalyzed() and not self.wants_abort:
                    sleep(2)
            i = i+1

    def image_clear(self):
        """ Clears canvas 
        """
        for ax in self.figure.get_axes(): 
            ax.cla()
        if not self.autoplot:
            self.figure.clear()
        
        wx.CallAfter(self.figure.canvas.draw)
    
def process(dataset_array, image_clear, figure):
    """ Function called to do the processing """
    global colors
    i=0
    image_clear()
    ax1=figure.add_axes([0.12,0.12,0.76,0.76])
        
    for set in dataset_array:
        if set.c == '':
            set.c = colors[i]
        if set.plotme == True and set.range != '':
            
            data = set.getdata_()
            
            datX, datY = (data[:,0], data[:,1])
            fitX, fitY =  set.fit1.fit(data)  if set.fit1.dofit or set.fit1.doplot else (None,None)
            
            if data !=None:
                
                if not set.X2 and not set.Y2:
                    ax1.set_xlabel(set.X,color=set.c)
                    ax1.set_ylabel(set.Y,color=set.c)
                    ax1.plot(datX,datY,'.',markersize=15, color=set.c)
                    
                    if fitX != None:
                        ax1.plot(fitX,fitY,'-', color=set.c)
                        
                if not set.X2 and set.Y2:
                    ax2 = ax1.twinx()
                    ax2.set_ylabel(set.Y,color=set.c)
                    ax2.plot(datX,datY,'.',markersize=15, color=set.c)
                    
                    if fitX != None:
                        ax2.plot(fitX,fitY,'-', color=set.c)
                        
                if set.X2 and not set.Y2:
                    ax2 = ax1.twiny()
                    ax2.set_xlabel(set.X,color=set.c)
                    ax2.plot(datX,datY,'.',markersize=15, color=set.c)
                    
                    if fitX!= None:
                        ax2.plot(fitX,fitY,'-', color=set.c)
                        
                if set.X2 and set.Y2:
                    ax2=ax1.figure.add_axes(ax1.get_position(True), frameon=False)
                    ax2.yaxis.tick_right()
                    ax2.yaxis.set_label_position('right')
                    ax2.yaxis.set_offset_position('right')
                    ax2.xaxis.tick_top()
                    ax2.xaxis.set_label_position('top')
                    
                    ax2.set_xlabel(set.X,color=set.c)
                    ax2.set_ylabel(set.Y,color=set.c)
                    ax2.plot(datX,datY,'.',markersize=15, color=set.c)
                    
                    if fitX!= None:
                        ax2.plot(fitX,fitY,'-', color=set.c)
        i = i + 1
    
    if figure.axes[0].yaxis.get_data_interval()[-1] > 1e3:
        figure.axes[0].yaxis.set_major_formatter( matplotlib.ticker.FormatStrFormatter('%.1e'))
        
    # figure.tight_layout()
        
    wx.CallAfter(figure.canvas.draw)

#-------------------------------------------------------------------------------#
#
#  MAIN WINDOW
#
#-------------------------------------------------------------------------------#

class MainWindowHandler(Handler):
    ## This handler is just graciously taking care of closing 
    ## the application when it is in the middle of doing a plot or a fit
    def init(self, info):
        if load_pck: 
            info.object._pck_(action='load')
            info.object._setfitexprs_()
    
    def close(self, info, is_OK):
        if ( info.object.process_thread
            and info.object.process_thread.isAlive() ):
            info.object.process_thread.wants_abort = True
            while info.object.process_thread.isAlive():
                sleep(0.1)
            wx.Yield()
        print 'i am closing down'
        try:
            info.object._pck_(action='save')
        except:
            pass
        return True

class MainWindow(HasTraits):
    """ The main window. """
    def _pck_(self,action,f=mainpck):
        if action == 'load':
            try:
                fpck=open(f,"rb")
                print 'Loading panel from %s' % f
                self.datasets = pickle.load(fpck)
            except:
                return
        if action == 'save':
            print 'Saving panel to %s' % f
            fpck=open(f,"w+b")
            pickle.dump(self.datasets,fpck)
        fpck.close()
    
    def _setfitexprs_(self):
        for set in self.datasets:
          set._setfitexprs_()

    #---- The figure that is shown on the left----#
    figure = Figure()

    #---- Objects that go in the CONTROL tab ----#
    clear = Button("clear")
    replot = Button("replot")
    savepck = Button("save pck")
    loadpck = Button("load pck")
    loadscan = Button("load scan")
    autoplot = Bool(False, desc="autoplotting: Check box to autplot", label="auto plotting") 
    datasets = List([ DataSet(name='Data1') ])
    selected = Instance(DataSet)
    index = Int
    addset = Button("Add data set")
    results_string = String()
    process_thread = Instance(ProcessThread)

    #---- Objects that go in the REPORT tab ----#
    repshot = Int(label='report shotnum')
    getreport = Button('get report')
    report =  String()

    #---- The view of the right pane is defined ----#
    control_group = Group(  
                  HGroup(Item('replot', show_label=False),
                         Item('clear', show_label=False ),
                         Item('autoplot', show_label=True ),
                         spring,
                         Item('savepck', show_label=False ),
                         Item('loadpck', show_label=False )),           
                  Item( '_' ),  
                  VGroup(                       
                       Item( 'datasets', style='custom', show_label=False,
                                                         editor = ListEditor( use_notebook=True,
                                                                              selected='selected',
                                                                              deletable=True,
                                                                              dock_style='tab', 
                                                                              page_name='.name')),
                       Item('addset', show_label=False),
                        ),
               )


    # The main view of the application is divided in two.  
    # A matplotlib plot is on the left and and the control_group is on the right
    view = View(HSplit(Item('figure', editor=MPLFigureEditor(), dock='vertical'),
                       control_group,
                       show_labels=False,
                      ),
                title = 'PLOTGUI :: Plot and Fit',
                resizable=True,
                height=0.75, width=0.75,
                handler=MainWindowHandler(),
                buttons=NoButtons)

    # Below are the callback definitions
    def _selected_changed(self,selected):
        self.index = self.datasets.index(selected)

    def _addset_fired(self):
        new = copy.deepcopy( self.datasets[ self.index ] ) 
        new.name = 'Data%s' % (1+len(self.datasets)) 
        self.datasets.append( new )

    def _clear_fired(self):
        """Callback of the "clear" button.  This stops the fitting thread if necessary
        and then clears the plot
        """
        if self.process_thread and self.process_thread.isAlive():
            self.process_thread.wants_abort = True
        else: 
            sleep(1)
            for ax in self.figure.get_axes(): 
              ax.cla()
            if not self.autoplot:
              self.figure.clear()
            print 'canvas cleared\n'
           

    def _autoplot_changed(self):
        if self.process_thread and self.process_thread.isAlive():
            self.process_thread.wants_abort = not self.autoplot

    def _replot_fired(self):
        """ Callback of the "replot" button. This starts
        the fitting thread, or kills it.
        """
        if self.process_thread and self.process_thread.isAlive():
            self.process_thread.wants_abort = True
        else:

            #---- The ProcessingThread is set up by giving it functions that
            #---- can alter the state of the Control Panel 
            self._setfitexprs_()
            self.process_thread = ProcessThread()
            self.process_thread.autoplot = self.autoplot           # Pass autoplot
            self.process_thread.figure = self.figure               # Pass the figure
            self.process_thread.datasets = self.datasets
            self.process_thread.start()                            # Start the fitting thread


    def _savepck_changed ( self ):
        """ Handles the user clicking the 'save pck...' button. Save the pck file to desired directory
        """ 
        file_name = save_file()
        if file_name != '':
            file_pck=open(file_name,"w+b")
            print 'Saving panel to pck.'
            self._pck_('save',file_pck)
            file_pck.close()

    def _loadpck_changed ( self ):
        """ Handles the user clicking the 'Open...' button. Load the pck file from desired directory
        """
        file_name = open_file()
        if file_name != '':
            print 'Loading panel from pck.'
            file_pck=open(file_name,"rb")
            self._pck_('load',file_pck)
            file_pck.close()
    

if __name__ == '__main__':
    MainWindow().configure_traits()


	
	
	
