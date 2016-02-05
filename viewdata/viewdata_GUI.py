#!/usr/bin/python
#view data version 2.0

import matplotlib
matplotlib.use('WXAgg')
import wx
import wx.lib.scrolledpanel as scrolled

from viewdata_core import *

from matplotlib.backends.backend_wx import NavigationToolbar2Wx

import os
import platform

if platform.system() == "Windows":
    # export ETS_TOOLKIT=qt4
    # ref: http://stackoverflow.com/questions/16350884/how-to-get-mayavi2-to-default-to-use-qt-rather-than-wx
    os.environ["ETS_TOOLKIT"] =  "wx"

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size = (1300, 600))

        self.mainpanel = wx.ScrolledWindow(self, -1)
        
        self.plotpanel = PlotPanel(self.mainpanel)
#        self.plotpanel.SetBackgroundColour('blue')
        self.controlpanel = ControlPanel(self.mainpanel)
#        self.controlpanel.SetBackgroundColour('red')
        
        self.replot = wx.Button(self.mainpanel, label = 'replot')
        self.Bind(wx.EVT_BUTTON, self.evt_press_replot, self.replot)
        
        self.vSizer = wx.BoxSizer(wx.VERTICAL)
        self.vSizer.Add(self.replot, 0, wx.EXPAND | wx.ALL, 5)
        self.vSizer.Add(self.controlpanel, 1, wx.EXPAND | wx.ALL, 5)
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(self.plotpanel, 1, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(self.vSizer, 0,  wx.EXPAND | wx.ALL, 5)
        self.mainpanel.SetSizer(mainSizer)

        self.mainpanel.SetScrollbars(1,1,1600,1200)
        
        self.Center()
        self.Show(True)
    
    def evt_press_replot(self, event):

        fig = self.plotpanel.fig
#        self.plotpanel.axes = []

#        gs = gridspec.GridSpec(gs_resolution,gs_resolution)
#see link: http://matplotlib.org/users/gridspec.html?highlight=subplot2grid for improvement.
#        gs.update(left = 0.02, right = 0.98, top =0.98, bottom = 0.02)
        PlotFigures(self.controlpanel.subplot_list, fig)
        #save before ploting
        self.controlpanel.subplot_list.save()



#        gs.tight_layout(self.plotpanel.fig)
#        self.controlpanel.subplot_list.gs.tight_layout(self.plotpanel.fig)

        self.plotpanel.canvas.draw()
        self.controlpanel.refresh_all(self.controlpanel.current_subplot,self.controlpanel.current_curve)


class PlotPanel(wx.Panel, PlotDataCore):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        PlotDataCore.__init__(self, parent)

        toolbar = NavigationToolbar2Wx( self.canvas )

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.EXPAND | wx.ALL) 
        self.vbox.Add(toolbar, 0, wx.EXPAND)
        self.SetSizer(self.vbox)

#    def add_subplot(self):
#        self.axes = self.fig.add_subplot(2,1,2)
#        self.canvas.draw()

class ControlPanel(wx.Panel):
    ''' class of ControlPanel, containing all the controls for the plot'''
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        #save/load setting button
        self.load_setup = wx.Button(self, label = "load")
        self.Bind(wx.EVT_BUTTON, self.evt_press_load_setup, self.load_setup)
        self.save_setup_as = wx.Button(self, label = "save as")
        self.Bind(wx.EVT_BUTTON, self.evt_press_save_setup_as, self.save_setup_as)
        self.save_setup = wx.Button(self, label = "save")
        self.Bind(wx.EVT_BUTTON, self.evt_press_save_setup, self.save_setup)


        self.subplot_list = Subplot_List()
        self.current_subplot = 0
        self.current_curve = 0

        #add/delete curve to a subplot
        self.add_curve = wx.Button(self, label = 'Add Setup')
        self.Bind(wx.EVT_BUTTON, self.evt_press_add_curve, self.add_curve)

        self.delete_curve = wx.Button(self, label = 'Del Setup')
        self.Bind(wx.EVT_BUTTON, self.evt_press_delete_curve, self.delete_curve)
        
        #add/delete subplot
        self.add_subplot = wx.Button(self, label = 'Add Subplot')
        self.Bind(wx.EVT_BUTTON, self.evt_press_add_subplot, self.add_subplot)

        self.delete_subplot = wx.Button(self, label = 'Del Subplot')
        self.Bind(wx.EVT_BUTTON, self.evt_press_delete_subplot, self.delete_subplot)

        #listboxes to choose curve or subplot
        self.choose_curve = wx.ListBox(self, size = (150,40), choices = [], style = wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX, self.evt_choose_curve, self.choose_curve)

        self.choose_subplot = wx.ListBox(self, size = (150,100), choices = [], style = wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX,self.evt_choose_subplot, self.choose_subplot)

        #setup of a subplot
        self.plotsubB = wx.CheckBox(self, label = 'Plot?')
        self.tex_name = wx.StaticText(self, label = "Name:")
        self.name = wx.TextCtrl(self, size = (130,30))
        self.tex_location = wx.StaticText(self, label = "Location:")
        self.location = wx.TextCtrl(self, size = (40,30))
        self.tex_subplot_num = wx.StaticText(self, label = "/")
        self.subplot_num = wx.TextCtrl(self, size = (40,30))
        
	self._tex_subplot_grid = wx.StaticText(self, label = "Subplot:")
        self._subplot_grid = wx.TextCtrl(self, size = (40,30))
        self.Bind(wx.EVT_TEXT, self.evt__subplot_grid_change, self._subplot_grid)

	self.tex_setup_grid = wx.StaticText(self, label = "Setup:")
        self.setup_grid = wx.TextCtrl(self, size = (40,30))
        
	#setup of a curve
        self.nb = wx.Notebook(self, size = (450,300))
        self.setup = Curve_Setup(self.nb)
        self.data = Curve_Data(self.nb)
        self.nb.AddPage(self.setup,"Setup")
        self.nb.AddPage(self.data, "Data")

        for elem in Subplot_setup_dict_type_default:
            bind_code = ''
            elem_type = Subplot_setup_dict_type_default[elem][0]
            if (elem_type != 'curve_list') & (elem != 'subplot_num'):
                if elem_type == 'bool':
                    event_string = 'EVT_CHECKBOX'
                elif (elem_type == 'string') | (elem_type == 'float') |(elem_type == 'int_list'):
                    event_string = 'EVT_TEXT'
                bind_code = 'self.Bind(wx.%s, self.evt_subplot_%s_change, self.%s)' %(event_string, elem, elem)
                exec bind_code
        
        for elem in Curve_setup_dict_type_default:
            bind_code = ''
            elem_type = Curve_setup_dict_type_default[elem][0]
            if (elem != 'fit_result') & (elem != 'data_str') & (elem != 'curve_num'):
                if elem_type == 'float_list':
                    event_string = 'EVT_TEXT'
                    bind_code = ''
                    for i in xrange(6):
                        bind_code = bind_code + 'self.Bind(wx.%s, self.evt_curve_%s_%d_change, self.setup.%s[%d])\n' %(event_string, elem, i, elem, i)
                else:
                    if elem_type == 'bool':
                        event_string = 'EVT_CHECKBOX'
                    elif (elem_type == 'string') | (elem_type == 'float') |(elem_type == 'int_list'):
                        if elem == 'func':
                            event_string = 'EVT_CHOICE'
                        else:
                            event_string = 'EVT_TEXT'
                    bind_code = 'self.Bind(wx.%s, self.evt_curve_%s_change, self.setup.%s)' %(event_string, elem, elem)
                exec bind_code

        #Layout of the control panel
        hSizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hSizer1.Add(self._tex_subplot_grid)
        hSizer1.Add(self._subplot_grid)
#        hSizer1.AddSpacer(10)
        hSizer1.Add(self.tex_setup_grid)
        hSizer1.Add(self.setup_grid)
        hSizer1.AddSpacer(10)
        hSizer1.Add(self.load_setup,  flag = wx.ALIGN_TOP, border = 50)
        hSizer1.Add(self.save_setup_as, 0, wx.RIGHT, 0)
        hSizer1.Add(self.save_setup, 0, wx.RIGHT, 0)

        vSizer22 = wx.BoxSizer(wx.VERTICAL)
        vSizer22.Add(self.add_subplot, 1, wx.ALL | wx.EXPAND, 0)
        vSizer22.Add(self.delete_subplot, 1, wx.ALL | wx.EXPAND, 0)
        vSizer22.Add(self.add_curve, 1, wx.ALL | wx.EXPAND, 0)
        vSizer22.Add(self.delete_curve, 1, wx.ALL | wx.EXPAND, 0)
        
        hSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hSizer2.Add(vSizer22, 0, wx.ALL, 5)
        hSizer2.Add(self.choose_subplot, 0, wx.ALL | wx.EXPAND, 5)
        hSizer2.Add(self.choose_curve, 1, wx.ALL | wx.EXPAND, 5)

        hSizer3 = wx.BoxSizer(wx.HORIZONTAL)
        hSizer3.Add(self.plotsubB)
        hSizer3.AddSpacer(20)
        hSizer3.Add(self.tex_name)
        hSizer3.Add(self.name )
        hSizer3.AddSpacer(20)
        hSizer3.Add(self.tex_location)
        hSizer3.Add(self.location)
        hSizer3.Add(self.tex_subplot_num)
        hSizer3.Add(self.subplot_num)
#        hSizer3.Add(self.tex_setup_grid)
#        hSizer3.Add(self.setup_grid)
        
	self.ln = wx.StaticLine(self, -1, size = (450,15), style = wx.LI_HORIZONTAL)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(hSizer1, 0, flag = wx.ALIGN_RIGHT)
        mainSizer.Add(hSizer2, 0, flag = wx.EXPAND)
        mainSizer.Add(hSizer3, 0, flag = wx.ALIGN_LEFT)
        mainSizer.Add(self.ln)
        mainSizer.Add(self.nb, 1, flag = wx.ALIGN_RIGHT, border = 0)
        self.SetSizer(mainSizer)
        
        self.refresh_all(0,0)
    
    def refresh_curve_listbox(self):
        choices = self.subplot_list.lst[self.current_subplot].get_name_list()
        self.choose_curve.DeselectAll()
        self.choose_curve.Clear()
        self.choose_curve.AppendItems(choices)

    def choose_curve_listbox(self, current_curve):
        list_length = len(self.subplot_list.lst[self.current_subplot].dic['curvelist'])
        if list_length == 0:
            self.current_curve = 0
        elif current_curve < 0:
            self.current_curve = list_length - 1
        elif current_curve < list_length:
            self.current_curve = current_curve
        else:
            self.current_curve = list_length - 1
        self.choose_curve.SetSelection(self.current_curve)
    
    def refresh_subplot_listbox(self):
        choices = self.subplot_list.get_name_list()
        self.choose_subplot.DeselectAll()
        self.choose_subplot.Clear()
        self.choose_subplot.AppendItems(choices)

    def choose_subplot_listbox(self, current_subplot):
        list_length = len(self.subplot_list.lst)
        if list_length == 0:
            self.current_subplot = 0
        elif current_subplot < 0:
            self.current_subplot = list_length - 1
        elif current_subplot < list_length:
            self.current_subplot = current_subplot
        else:
            self.current_subplot = list_length - 1
        self.choose_subplot.SetSelection(self.current_subplot)

    def refresh_subplot_setup(self, subplot):
        dic = subplot.dic
        for elem in dic:
            elem_type = Subplot_setup_dict_type_default[elem][0]
            if elem_type == 'string':
                refresh_code = 'self.%s.ChangeValue(dic["%s"])' %(elem, elem)
            elif elem_type == 'float':
                string = subplot.get_str(elem)
                refresh_code = 'self.%s.ChangeValue(string)' %elem
            elif elem_type == 'bool':
                refresh_code = 'self.%s.SetValue(dic["%s"])' %(elem,elem)
            elif elem_type == 'int_list':
                string = subplot.get_str(elem)
                refresh_code = 'self.%s.ChangeValue(string)' %elem
            elif elem_type == 'curve_list':
                    refresh_code = 'pass'
            else:
                refresh_code = 'print "Error: no control for element", elem, "!"'
            exec refresh_code
    
    def refresh_curve_setup(self, curve):
        dic = curve.dic
        for elem in dic:
            elem_type = Curve_setup_dict_type_default[elem][0]
            if elem_type == 'string':
                if elem == 'func':
                    refresh_code = 'self.setup.func.SetStringSelection(dic["func"])'
                elif elem == 'data_str':
                    refresh_code = 'self.data.data_str.ChangeValue(dic["data_str"])'
                else:
                    refresh_code = 'self.setup.%s.ChangeValue(dic["%s"])' %(elem, elem)
            elif elem_type == 'float':
                string = curve.get_str(elem)
                refresh_code = 'self.setup.%s.ChangeValue(string)' %elem
            elif elem_type == 'bool':
                refresh_code = 'self.setup.%s.SetValue(dic["%s"])' %(elem,elem)
            elif elem_type == 'int_list':
                string = curve.get_str(elem)
                refresh_code = 'self.setup.%s.ChangeValue(string)' %elem
            elif elem_type == 'float_list':
                if elem == 'para_list':
                    string = curve.get_str(elem)
                    refresh_code = ''
                    for i in xrange(6):
                        string = str(dic[elem][i])
                        refresh_code = refresh_code + 'self.setup.para_list[%d].ChangeValue("%s")\n' %(i,string)
                else:
                    refresh_code = 'print "Error: no such element!"'
            else:
                refresh_code = 'print "Error: no control for element", elem, "!"'
            exec refresh_code

    def refresh_all(self, new_subplot_index, new_curve_index):
	self._subplot_grid.ChangeValue(','.join(map(str,self.subplot_list.subplot_grid)))
        self.refresh_subplot_listbox()
        self.choose_subplot_listbox(new_subplot_index)
        
        self.refresh_subplot(new_curve_index)

    def refresh_subplot(self, new_curve_index):
        self.refresh_curve_listbox()
        self.choose_curve_listbox(new_curve_index)
        
        subplot = self.subplot_list.lst[self.current_subplot]
        self.refresh_subplot_setup(subplot)
        self.refresh_curve()

    def refresh_curve(self):
        curve = self.subplot_list.lst[self.current_subplot].dic['curvelist'][self.current_curve]
        self.refresh_curve_setup(curve)

    
    def evt_press_load_setup(self, event):
        dlg = wx.FileDialog(self, "Choose a file to load from:", style = wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            new_dir = dlg.GetPath()
        else:
            new_dir = 0
        dlg.Destroy()
        
        if new_dir != 0:
            self.subplot_list.load(new_dir)
            if len(self.subplot_list.lst) == 0:
                self.subplot_list.add_subplot()
            self.refresh_all(0,0)

    def evt_press_save_setup_as(self, event):
        dlg = wx.FileDialog(self, "Choose a file to save to:", style = wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            directory = dlg.GetPath()
        else:
            directory = 0
        dlg.Destroy()

        self.subplot_list.save(directory)
        
    def evt_press_save_setup(self, event):
        self.subplot_list.save()
        
    def evt_press_add_subplot(self, event):
        new_subplot = copy.deepcopy(self.subplot_list.lst[self.current_subplot])
        self.subplot_list.add_subplot(new_subplot)
        self.refresh_all(-1,0)
    
    def evt_press_delete_subplot(self, event):
        self.subplot_list.del_subplot(self.current_subplot)
        if len(self.subplot_list.lst) == 0:
            self.subplot_list.add_subplot()
        self.refresh_all(self.current_subplot,0)
    
    def evt_press_add_curve(self, event):
        new_curve = copy.deepcopy(self.subplot_list.lst[self.current_subplot].dic['curvelist'][self.current_curve])
        self.subplot_list.lst[self.current_subplot].add_curve(new_curve)
        self.refresh_all(self.current_subplot,-1)
    
    def evt_press_delete_curve(self, event):
        self.subplot_list.lst[self.current_subplot].del_curve(self.current_curve)
        if len(self.subplot_list.lst[self.current_subplot].dic['curvelist']) == 0:
            self.subplot_list.lst[self.current_subplot].add_curve()
        self.refresh_all(self.current_subplot,self.current_curve)


    def evt_choose_subplot(self, event):
        self.current_subplot = self.choose_subplot.GetSelections()[0]
        self.refresh_subplot(0)

    def evt_choose_curve(self, event):
        self.current_curve = self.choose_curve.GetSelections()[0]
        self.refresh_curve()

    
    def update_subplot_elem(self, elem):
        update_code = ''
        elem_type = Subplot_setup_dict_type_default[elem][0]
        subplot = self.subplot_list.lst[self.current_subplot]
        update_code = 'subplot.set_value("%s", str(self.%s.GetValue()))' %(elem,elem)
        exec update_code
#        print elem, subplot.dic[elem]
    
    def update_curve_elem(self, elem, index = 0):
        update_code = ''
        elem_type = Curve_setup_dict_type_default[elem][0]
        curve = self.subplot_list.lst[self.current_subplot].dic['curvelist'][self.current_curve]
        if elem_type == 'float_list':
            update_code = 'curve.set_value("%s", str(self.setup.%s[%d].GetValue()),index)' %(elem, elem, index)
        else:
            if elem == 'func':
                update_code = 'curve.set_value("%s", str(self.setup.%s.GetStringSelection()))' %(elem,elem)
            else:
                update_code = 'curve.set_value("%s", str(self.setup.%s.GetValue()))' %(elem,elem)
        exec update_code
#        print elem, curve.dic[elem]

    
    def evt__subplot_grid_change(self,event):
	subplot_grid_str = self._subplot_grid.GetValue().split(',')
	if (len(subplot_grid_str) == 2):
	    if (subplot_grid_str[1] != ''):
	        self.subplot_list.subplot_grid = map(int, subplot_grid_str)
                self.subplot_list.get_stat()
                string = self.subplot_list.lst[self.current_subplot].get_str('subplot_num')
                self.subplot_num.ChangeValue(string)

    def evt_subplot_name_change(self, event):
        self.update_subplot_elem('name')
        self.refresh_subplot_listbox()
        self.choose_subplot_listbox(self.current_subplot)

    def evt_subplot_setup_grid_change(self, event):
        self.update_subplot_elem('setup_grid')
        self.subplot_list.lst[self.current_subplot].get_stat()
        string = self.subplot_list.lst[self.current_subplot].dic['curvelist'][self.current_curve].get_str('curve_num')
        self.setup.curve_num.ChangeValue(string)
    
    def evt_subplot_location_change(self, event):
        self.update_subplot_elem('location')
        self.subplot_list.get_stat()
        string = self.subplot_list.lst[self.current_subplot].get_str('subplot_num')
        self.subplot_num.ChangeValue(string)

    def evt_subplot_plotsubB_change(self, event):
        self.update_subplot_elem('plotsubB')
        self.subplot_list.get_stat()
        string = self.subplot_list.lst[self.current_subplot].get_str('subplot_num')
        self.subplot_num.ChangeValue(string)

    
    def evt_curve_name_change(self, event):
        self.update_curve_elem('name')
        self.refresh_curve_listbox()
        self.choose_curve_listbox(self.current_curve)

    def evt_curve_location_change(self, event):
        self.update_curve_elem('location')
        self.subplot_list.lst[self.current_subplot].get_stat()
        string = self.subplot_list.lst[self.current_subplot].dic['curvelist'][self.current_curve].get_str('curve_num')
        self.setup.curve_num.ChangeValue(string)

    def evt_curve_plotcurveB_change(self, event):
        self.update_curve_elem('plotcurveB')
        self.subplot_list.lst[self.current_subplot].get_stat()
        string = self.subplot_list.lst[self.current_subplot].dic['curvelist'][self.current_curve].get_str('curve_num')
        self.setup.curve_num.ChangeValue(string)

    def evt_curve_date_change(self, event):
        self.update_curve_elem('date')

    def evt_curve_shots_change(self, event):
        self.update_curve_elem('shots')
    
    def evt_curve_X_change(self, event):
        self.update_curve_elem('X')
    
    def evt_curve_Y_change(self, event):
        self.update_curve_elem('Y')
    
    def evt_curve_Xl_change(self, event):
        self.update_curve_elem('Xl')
    
    def evt_curve_Xmin_change(self, event):
        self.update_curve_elem('Xmin')
    
    def evt_curve_Xmax_change(self, event):
        self.update_curve_elem('Xmax')
    
    def evt_curve_Yl_change(self, event):
        self.update_curve_elem('Yl')
    
    def evt_curve_Ymin_change(self, event):
        self.update_curve_elem('Ymin')
    
    def evt_curve_Ymax_change(self, event):
        self.update_curve_elem('Ymax')
    
    def evt_curve_Legend_change(self, event):
        self.update_curve_elem('Legend')
    
    def evt_curve_color_change(self, event):
        self.update_curve_elem('color')
    
    def evt_curve_ec_change(self, event):
        self.update_curve_elem('ec')
    
    def evt_curve_fmt_change(self, event):
        self.update_curve_elem('fmt')
    
    def evt_curve_ms_change(self, event):
        self.update_curve_elem('ms')

    def evt_curve_mew_change(self, event):
        self.update_curve_elem('mew')

    def evt_curve_matchB_change(self, event):
        self.update_curve_elem('matchB')

    def evt_curve_statsB_change(self, event):
        self.update_curve_elem('statsB')

    def evt_curve_gridB_change(self, event):
        self.update_curve_elem('gridB')

    def evt_curve_logxB_change(self, event):
        self.update_curve_elem('logxB')

    def evt_curve_logyB_change(self, event):
        self.update_curve_elem('logyB')

    def evt_curve_xticksB_change(self, event):
        self.update_curve_elem('xticksB')

    def evt_curve_yticksB_change(self, event):
        self.update_curve_elem('yticksB')

    def evt_curve_plotfuncB_change(self, event):
        self.update_curve_elem('plotfuncB')

    def evt_curve_fitB_change(self, event):
        self.update_curve_elem('fitB')

    def evt_curve_func_change(self, event):
        self.update_curve_elem('func')
        curve = self.subplot_list.lst[self.current_subplot].dic['curvelist'][self.current_curve]
        self.setup.function = fitdict[curve.dic['func']]
        self.setup.tex_function.SetLabel('f(x) = ' + self.setup.function.fitexpr)

    def evt_curve_para_list_0_change(self, event):
        self.update_curve_elem('para_list', 0)

    def evt_curve_para_list_1_change(self, event):
        self.update_curve_elem('para_list', 1)

    def evt_curve_para_list_2_change(self, event):
        self.update_curve_elem('para_list', 2)

    def evt_curve_para_list_3_change(self, event):
        self.update_curve_elem('para_list', 3)

    def evt_curve_para_list_4_change(self, event):
        self.update_curve_elem('para_list', 4)

    def evt_curve_para_list_5_change(self, event):
        self.update_curve_elem('para_list', 5)


class Curve_Setup(scrolled.ScrolledPanel):
    def __init__(self, parent):
        super(Curve_Setup, self).__init__(parent = parent, id = wx.ID_ANY)
        
        self.plotcurveB = wx.CheckBox(self, label = 'Plot?')
        self.tex_name = wx.StaticText(self, label = "Name:")
        self.name = wx.TextCtrl(self, size = (130,30))
        self.tex_location = wx.StaticText(self, label = "Location:")
        self.location = wx.TextCtrl(self, size = (40,30))
        self.tex_curve_num = wx.StaticText(self, label = "/")
        self.curve_num = wx.TextCtrl(self, size = (40,30))
        
        hSizer0 = wx.BoxSizer(wx.HORIZONTAL)
        hSizer0.Add(self.plotcurveB)
        hSizer0.AddSpacer(20)
        hSizer0.Add(self.tex_name)
        hSizer0.Add(self.name)
        hSizer0.AddSpacer(20)
        hSizer0.Add(self.tex_location)
        hSizer0.Add(self.location)
        hSizer0.Add(self.tex_curve_num)
        hSizer0.Add(self.curve_num)
        
        self.tex_date = wx.StaticText(self, label = "Date:")
        self.date = wx.TextCtrl(self, size = (150,30))

        self.tex_shots = wx.StaticText(self, label = "Shots:")
        self.shots = wx.TextCtrl(self, size = (370,30))
        
        self.tex_X = wx.StaticText(self, label = "X:")
        self.X = wx.TextCtrl(self, size = (370,30))

        self.tex_Y = wx.StaticText(self, label = "Y:")
        self.Y = wx.TextCtrl(self, size = (370,30))

        grid1 = wx.GridBagSizer(hgap = 5, vgap = 5)
        grid1.Add(self.tex_date, pos = (0,0))
        grid1.Add(self.date, pos = (0,1))
        grid1.Add(self.tex_shots, pos = (1,0))
        grid1.Add(self.shots, pos = (1,1))
        grid1.Add(self.tex_X, pos = (2,0))
        grid1.Add(self.X, pos = (2,1))
        grid1.Add(self.tex_Y, pos = (3,0))
        grid1.Add(self.Y, pos = (3,1))
        
        
        grid0  = wx.FlexGridSizer(1, 6, 7, 15)
        self.statsB  =  wx.CheckBox(self, label="stats")
        self.gridB   =  wx.CheckBox(self, label="grid")
        self.logxB   =  wx.CheckBox(self, label="logx")
        self.logyB   =  wx.CheckBox(self, label="logy")
        self.xticksB =  wx.CheckBox(self, label="xticks")
        self.yticksB =  wx.CheckBox(self, label="yticks")
        grid0.AddMany([(self.statsB), (self.gridB), (self.logxB), (self.logyB), (self.xticksB), (self.yticksB) ])
       
       
        grid2 = wx.FlexGridSizer(2, 6, 9, 15)
        self.optxlab = wx.StaticText(self, label="Xl")
        self.optxmin = wx.StaticText(self, label="Xmin")
        self.optxmax = wx.StaticText(self, label="Xmax")

        self.optylab = wx.StaticText(self, label="Yl")
        self.optymin = wx.StaticText(self, label="Ymin")
        self.optymax = wx.StaticText(self, label="Ymax")

        self.Xl = wx.TextCtrl(self)
        self.Xmin = wx.TextCtrl(self)
        self.Xmax = wx.TextCtrl(self)
        self.Yl = wx.TextCtrl(self)
        self.Ymin = wx.TextCtrl(self)
        self.Ymax = wx.TextCtrl(self)

        grid2.AddMany([
         (self.optxlab), (self.Xl, 2, wx.EXPAND), (self.optxmin), (self.Xmin), (self.optxmax), (self.Xmax),
         (self.optylab), (self.Yl, 2, wx.EXPAND), (self.optymin), (self.Ymin), (self.optymax), (self.Ymax)])
        grid2.AddGrowableCol(1, 1)

        grid3 = wx.FlexGridSizer(1, 2, 9, 15)
        self.optleg = wx.StaticText(self, label="Legend")
        self.Legend = wx.TextCtrl(self, size = (350,30))
        grid3.AddMany([(self.optleg), (self.Legend)])
        grid3.AddGrowableCol(1, 1)

        grid4 = wx.FlexGridSizer(2,6, 9, 15)
        self.optec  = wx.StaticText(self, label="fc")
        self.optfc  = wx.StaticText(self, label="ec")
        self.optfmt = wx.StaticText(self, label="fmt")
        self.optms  = wx.StaticText(self, label="ms")
        self.optmew = wx.StaticText(self, label="mew")
        self.dummy = wx.StaticText(self, label="")

        self.color = wx.TextCtrl(self)
        self.ec = wx.TextCtrl(self)
        self.fmt = wx.TextCtrl(self)
        self.ms = wx.TextCtrl(self)
        self.mew = wx.TextCtrl(self)
        self.matchB =  wx.CheckBox(self, label="match?")
        grid4.AddMany([(self.optec), (self.color, 1, wx.EXPAND),
                      (self.optfc), (self.ec, 1, wx.EXPAND),
                      (self.matchB), (self.dummy),
                      (self.optfmt), (self.fmt, 1, wx.EXPAND),
                      (self.optms), (self.ms, 1, wx.EXPAND),
                      (self.optmew), (self.mew, 1, wx.EXPAND),
                      ])
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(5)
        vbox.Add(hSizer0)
        vbox.AddSpacer(5)
        vbox.Add(grid0)
        vbox.AddSpacer(5)
        vbox.Add(grid1)
        vbox.AddSpacer(5)
        vbox.Add(grid2)
        vbox.AddSpacer(5)
        vbox.Add(grid3)
        vbox.AddSpacer(5)
        vbox.Add(grid4)


        self.ln = wx.StaticLine(self, -1, size = (420,15), style = wx.LI_HORIZONTAL)
        vbox.Add(self.ln)

        self.plotfuncB   =  wx.CheckBox(self, label="plotfunc?")
        self.fitB   =  wx.CheckBox(self, label="fit?")

        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.AddSpacer(20)
        hbox0.Add(self.plotfuncB)
        hbox0.AddSpacer(30)
        hbox0.Add(self.fitB)

        self.tex_func = wx.StaticText(self, label = "Func:")
        self.func = wx.Choice(self, choices = fitdict.keys())
        hbox0.AddSpacer(30)
        hbox0.Add(self.tex_func)
        hbox0.AddSpacer(10)
        hbox0.Add(self.func)

        self.tex_function = wx.StaticText(self, label = "f(x) = ")
        
        vbox3 = wx.BoxSizer(wx.VERTICAL)
        self.para_list = []
        for i in xrange(6):
            text = wx.TextCtrl(self, size = (70, 30))
            self.para_list.append(text)
            vbox3.Add(text)
        
        self.fit_result = wx.TextCtrl(self, size = (250, 180), style = wx.TE_READONLY | wx.TE_MULTILINE)

        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4.Add(vbox3)
        hbox4.AddSpacer(20)
        hbox4.Add(self.fit_result)
        
        vbox.AddSpacer(10)
        vbox.Add(hbox0)
        vbox.AddSpacer(10)
        vbox.Add(self.tex_function)
        vbox.AddSpacer(10)
        vbox.Add(hbox4)
        self.SetSizerAndFit(vbox)
        self.SetupScrolling()

class Curve_Data(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.data_str = wx.TextCtrl(self, style = wx.TE_MULTILINE)
        self.data_str.SetEditable(False)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.data_str, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizerAndFit(sizer)


def run_GUI():
    app = wx.App(False)
    frame = MainWindow(parent = None, title = "view data 2.1")
    app.MainLoop()


if __name__ == '__main__':
    run_GUI()

#    curve1 = Curve()
#    curve1.set_value('location', '1,8')
#    curve1.set_value('name', 'my new')
#
##    for elem in curve1.dic:
##        print '%s is: ' %elem, curve1.get_str(elem)
#
##    print curve1.get_str_dic()
##    for i in xrange(2):
##        print 'para_list[%d]: ' %i, curve1.get('location', i)
#    subplot1 = Subplot()
#    subplot1.add_curve()
#    subplot1.add_curve()
#    subplot1.add_curve(curve1)
#
#    config = ConfigObj()
#    config.filename = 'new_setting.INI'
#    config['1st section'] = subplot1.get_str_dic()
#    config.write()
#
#    config = ConfigObj('./new_setting.INI')
##    print config['1st section']['curve 1']['name']
#    subplot1.set_str_dic(config['1st section'])
#    print subplot1.dic['curvelist'][0].dic
#    print subplot1.dic['curvelist'][1].dic
#    print subplot1.dic['curvelist'][2].dic
    
#    subplot_list1 = Subplot_List()
#    subplot_list1.load()
#    for elem in subplot_list1.lst:
#        print elem.get_str_dic()
