from threading import Thread
from time import sleep
from enthought.traits.api import *
from enthought.traits.ui.api import View, Item, Group, HGroup, VGroup, HSplit, VSplit,Handler, CheckListEditor, EnumEditor, ListStrEditor,ArrayEditor, spring
from enthought.traits.ui.menu import NoButtons
from enthought.traits.ui.file_dialog import save_file,open_file
from enthought.chaco.api import Plot, ArrayPlotData
from enthought.enable.component_editor import ComponentEditor
from enthought.chaco.chaco_plot_editor import ChacoPlotItem
from mpl_figure_editor import MPLFigureEditor
from matplotlib.figure import Figure
from scipy import * 
from numpy import loadtxt, linspace, sin
import wx
from random import choice
from configobj import ConfigObj

from qrange import qrange

import numpy
import matplotlib
import pickle
from configobj import ConfigObj

from fitlibrary import Fits

global display
global colors 
colors = ['#0D8800','#1729E0','#00A779','#D8005F','green','red','magenta','black']

#-------------------------------------------------------------------------------#
#
#  HELPER FUNCTIONS
#
#-------------------------------------------------------------------------------#

import plotconf 
plotconfini, path =  plotconf.initplotgui()

# The correct paths are stored in the plotconfini.INI file
def LastAnalyzed():
    LASTNUM = ConfigObj(plotconfini)['DIRECTORIES']['lastnum']
    if LASTNUM[0] != '/':
      LASTNUM = path + '/' + LASTNUM
    file = open( LASTNUM,'r')
    lastnum = int( file.readline() )
    file.close()
    return lastnum

def DataDir():
    SAVEDIR = ConfigObj(plotconfini)['DIRECTORIES']['savedirfile']
    if SAVEDIR[0] != '/':
      SAVEDIR = path + '/' + SAVEDIR
    savedirfile = open( SAVEDIR,'r')
    savedir = savedirfile.readline()
    savedirfile.close()
    return savedir

#-------------------------------------------------------------------------------#
#
#  DATA SET
#
#-------------------------------------------------------------------------------#

class DataSet(HasTraits):
    """ Object that holds the information defining a data set"""
    def _pck_(self,action,fpck):
       if action == 'save':
           pickle.dump( self.X, fpck)
           pickle.dump( self.Y, fpck )
           pickle.dump( self.c, fpck )
           pickle.dump( self.datadir, fpck )
           pickle.dump( self.range, fpck )
           fit_a = [self.fit1]
           for f in fit_a:
               f._pck_(action,fpck)
       if action == 'load':
           self.X =  pickle.load( fpck)
           self.Y = pickle.load( fpck )
           self.c = pickle.load( fpck )
           self.datadir = pickle.load( fpck )
           self.range = pickle.load( fpck )           
           fit_a = [self.fit1]
           for f in fit_a:
               f._pck_(action,fpck)
           
    def _setfitexprs_(self):
        self.fit1._setfitexprs_()


    plotme = Bool(False, label="plot me ?")
    X2 = Bool(False, label="X2?")
    Y2 = Bool(False, label="Y2?")
    
    X = Str('TRAPFREQ:modfreq', label="X")
    Y = Str('CPP:ax0w', label="Y")
   
    c = Str('', label="Color") 

    datadir = Str( DataDir(), label="DataDir", desc="directory where reports are located")
    range = Str( '', label="Range", desc="range of data to be plotted")

    fit1 = Instance(Fits, ())

    raw_data = String()
    saveraw = Button('Save Raw Data')
    loadscan = Button('Load Scan')
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
                               Item('saveraw',show_label=False),label='Raw Data')
                                   ,dock='tab', height=600
              )

    def getdata_(self):
       """ Executes qrange to extract data from reports. 
       """
       data, errmsg, rawdat = qrange(self.datadir, self.range, self.X + " " + self.Y)
       display(errmsg)
       self.raw_data = rawdat
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
        INFO = ConfigObj(plotconfini)['DIRECTORIES']['infofile']
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
                display("Processing to slow")
                return
        except AttributeError:
            pass
        self.processing_job = Thread(target=process, args=(dataset_array, image_clear, figure))
        self.processing_job.start()

    def run(self):
        """ Runs the fitting loop. """
        i=0
        while not self.wants_abort:
            self.process([self.dat1,self.dat2,self.dat3,self.dat4,self.dat5], self.image_clear, self.figure)
            if i==0:
                self.wants_abort = not self.autoplot
            if i>0 and not self.wants_abort: 
                p0= LastAnalyzed()
                while p0 == LastAnalyzed() and not self.wants_abort:
                    sleep(2)
            i = i+1


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
            fitX, fitY =  set.fit1.fit(data)  if set.fit1.dofit else (None,None)
            
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
        
    wx.CallAfter(figure.canvas.draw)

#-------------------------------------------------------------------------------#
#
#  CONTROL PANEL
#
#-------------------------------------------------------------------------------#

class ControlPanel(HasTraits):
    """ This object is the core of the traitsUI interface. Its view is
    the right panel of the application, and it hosts the method for
    interaction between the objects and the GUI.
    """
    
    def _pck_(self,action,fpck):
        self.dat1._pck_(action,fpck)
        self.dat2._pck_(action,fpck)
        self.dat3._pck_(action,fpck)
        self.dat4._pck_(action,fpck)
        self.dat5._pck_(action,fpck)
    
    def _setfitexprs_(self):
        self.dat1._setfitexprs_()
        self.dat2._setfitexprs_()
        self.dat3._setfitexprs_()
        self.dat4._setfitexprs_()
        self.dat5._setfitexprs_()

    #---- Objects that go in the CONTROL tab ----#

    figure = Instance(Figure)
 
    clear = Button("clear")
    replot = Button("replot")
    savepck = Button("save pck")
    loadpck = Button("load pck")
    loadscan = Button("load scan")
    autoplot = Bool(False, desc="autoplotting: Check box to autplot", label="auto plotting")

    dat1 = Instance(DataSet, ())
    dat2 = Instance(DataSet, ())
    dat3 = Instance(DataSet, ())
    dat4 = Instance(DataSet, ())
    dat5 = Instance(DataSet, ()) 

    results_string = String()
        
    process_thread = Instance(ProcessThread)

    #---- Objects that go in the REPORT tab ----#

    repshot = Int(label='report shotnum')
    getreport = Button('get report')
    report =  String()


    view = View(  
                  HGroup(Item('replot', show_label=False),
                         Item('clear', show_label=False ),
                         Item('autoplot', show_label=True ),
                         spring,
                         Item('savepck', show_label=False ),
                         Item('loadpck', show_label=False )),           
                  Item( '_' ),  
                  VSplit(                       
                       Item ('results_string',show_label=False, springy=True, style='custom'),
                       Group(Item('dat1', style='custom', show_label=False),
                             Item('dat2', style='custom', show_label=False),
                             Item('dat3', style='custom', show_label=False),
                             Item('dat4', style='custom', show_label=False),
                             Item('dat5', style='custom', show_label=False),                                     
                             layout='tabbed', springy=True),
                        ),
               )


    def _clear_fired(self):
        """Callback of the "clear" button.  This stops the fitting thread if necessary
        and then clears the plot
        """
        if self.process_thread and self.process_thread.isAlive():
            self.process_thread.wants_abort = True
        else: 
            sleep(1)
            self.image_clear()
            self.add_line('canvas cleared')
           

    def _autoplot_changed(self):
        if self.process_thread and self.process_thread.isAlive():
            self.process_thread.wants_abort = not self.autoplot

    def _replot_fired(self):
        """ Callback of the "replot" button. This starts
        the fitting thread, or kills it.
        """
        global display
        if self.process_thread and self.process_thread.isAlive():
            self.process_thread.wants_abort = True
        else:

            #---- The ProcessingThread is set up by giving it functions that
            #---- can alter the state of the Control Panel 
            self._setfitexprs_()
            self.process_thread = ProcessThread()
            self.process_thread.autoplot = self.autoplot           # Pass autoplot
            display = self.add_line                                # Make the status update function global
            self.process_thread.image_clear = self.image_clear     # Pass the function to clear the plot
            self.process_thread.image_show = self.image_show       # Pass the function to show the plot
            self.process_thread.figure = self.figure               # Pass the figure
            #self.process_thread.dats = [self.dat1, self.dat2]                   # Pass the data sets
            self.process_thread.dat1 = self.dat1                   # Pass the data sets
            self.process_thread.dat2 = self.dat2                   # Pass the data sets
            self.process_thread.dat3 = self.dat3                   # Pass the data sets
            self.process_thread.dat4 = self.dat4                   # Pass the data sets
            self.process_thread.dat5 = self.dat5                   # Pass the data sets
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
    
    def add_line(self, string):
        """ Adds a line to the textbox display.
        """
        self.results_string = (string + "\n" + self.results_string)[0:1000]

    def image_clear(self):
        """ Clears canvas 
        """
        for ax in self.figure.get_axes(): 
            ax.cla()
        if not self.autoplot:
            self.figure.clear()
        
        wx.CallAfter(self.figure.canvas.draw)
    
    def image_show(self, data):
        """ Plots an image on the canvas
        """
        self.image_clear()
        if not self.autoplot:
            self.figure.add_axes([0.1,0.1,0.8,0.8])
        self.figure.axes[0].set_title("[" + self.shots.datadir + " " + str(self.shots.shot0) + " " + str(self.shots.shotf) + "]\n" + self.shots.title)
        c = ['#0D8800','#1729E0','#00A779','#D8005F','green','red','magenta','black']
        self.figure.axes[0].set_xlabel(self.keys.X)
        plotcolor = choice(c)
        c.remove(plotcolor)
        self.figure.axes[0].set_ylabel( self.keys.y1keys(0), color=plotcolor )
        for i in range (self.keys.Y1N()):
            self.figure.axes[0].plot(data[:,0],data[:,i+1],'.',markersize=15, color=plotcolor)
            plotcolor = choice(c)
            c.remove(plotcolor)
        if self.keys.Y2N() > 0:
            y2 = self.figure.axes[0].twinx()
            y2.set_ylabel( self.keys.y2keys(0) , color=plotcolor) 
            ny1=self.keys.Y1N()
            for i in range (self.keys.Y2N()):
                y2.plot( data[:,0], data[:,i+1+ny1],'.',markersize=15, color=plotcolor)
                plotcolor = choice(c)
                c.remove(plotcolor) 
        wx.CallAfter(self.figure.canvas.draw)

#-------------------------------------------------------------------------------#
#
#  MAIN WINDOW
#
#-------------------------------------------------------------------------------#

class MainWindowHandler(Handler):
    ## This handler is just graciously taking care of closing 
    ## the application when it is in the middle of doing a plot or a fit
    def init(self, info):
        info.object._pck_(action='load')
        info.object.panel._setfitexprs_()
    
    def close(self, info, is_OK):
        if ( info.object.panel.process_thread
            and info.object.panel.process_thread.isAlive() ):
            info.object.panel.process_thread.wants_abort = True
            while info.object.panel.process_thread.isAlive():
                sleep(0.1)
            wx.Yield()
        print 'i am closing down'
        try:
            info.object._pck_(action='save')
        except:
            pass
        return True

class MainWindow(HasTraits):
    """ The main window, here go the instructions to create and destroy the application. """
    figure = Instance(Figure)
    panel = Instance(ControlPanel)

    def _figure_default(self):
        figure = Figure()
        return figure

    def _panel_default(self):
        return ControlPanel(figure=self.figure)
        
    def _pck_(self,action,f='viewdata_win.pck'):
        if action == 'load':
            try:
                fpck=open(f,"rb")
                print 'Loading panel from pck.'
            except:
                return
        if action == 'save':
            print 'Saving panel to pck.'
            fpck=open(f,"w+b")
        self.panel._pck_(action,fpck)
        fpck.close()

    # The main view of the application is divided in two.  
    # A matplotlib plot is on the left and an instance of ControlPanel is on the right
    view = View(HSplit(Item('figure', editor=MPLFigureEditor(), dock='vertical'),
                       Item('panel', style="custom"),
                       show_labels=False,
                      ),
                title = 'PLOTGUI :: Plot and Fit',
                resizable=True,
                height=0.75, width=0.75,
                handler=MainWindowHandler(),
                buttons=NoButtons)





	



if __name__ == '__main__':
    MainWindow().configure_traits()


	
	
	
