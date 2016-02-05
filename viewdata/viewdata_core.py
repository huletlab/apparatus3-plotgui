import copy
import matplotlib.gridspec as gridspec
from configobj import ConfigObj
try:
    from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
    from matplotlib.figure import Figure
except SystemExit:
    print "GUI module not loaded properly!!"

from scipy import stats

import qrange
import statdat
#from fitlibrary import *
from fitlibrary import *
import matplotlib.pyplot as plt

data_dir = '/lab/data/app3'
new_setting_dir = './new_setting.INI'
gs_resolution = 720

#'''This dictionary define the types and default values for the elements in dictionary Curve_Setup_Dic.dic. Each word has a formate of : element_name:[type_string, default_value_string]. Dictionary Curve_Setup_Dic has and only has these elements in this dictionary'''
Curve_setup_dict_type_default = {'name': ['string', 'new curve'], 'plotcurveB': ['bool', True],
                                 'location': ['int_list', [1, 1]], 'date': ['string', '2014/03/03'],
                                 'shots': ['string', '8163:8196'], 'X': ['string', 'SEQ:shot'],
                                 'Y': ['string', 'MOT:goal'], 'Xl': ['string', ''], 'Xmin': ['float', None],
                                 'Xmax': ['float', None], 'Yl': ['string', ''], 'Ymin': ['float', None],
                                 'Ymax': ['float', None], 'Legend': ['string', ''], 'color': ['string', "auto"],
                                 'ec': ['string', 'black'], 'fmt': ['string', 'o'], 'ms': ['float', None],
                                 'mew': ['float', None], 'matchB': ['bool', True], 'statsB': ['bool', False],
                                 'gridB': ['bool', False], 'logxB': ['bool', False], 'logyB': ['bool', False],
                                 'xticksB': ['bool', True], 'yticksB': ['bool', True], 'plotfuncB': ['bool', False],
                                 'fitB': ['bool', False], 'func': ['string', 'Parabola'],
                                 'para_list': ['float_list', [0, 0, 0, 0, 0, 0]], 'fit_result': ['string', ''],
                                 'data_str': ['string', ''], 'curve_num': ['int_list', [1, 1]]}

Subplot_setup_dict_type_default = {'name': ['string', 'new subplot'], 'location': ['int_list', [1, 1]],
                                   'plotsubB': ['bool', True], 'curvelist': ['curve_list', []],
                                   'subplot_num': ['int_list', [1, 1]], 'setup_grid': ['int_list', [1, 1]]}

def set_default_curve_date(year, month, day):
    date = "{year:04}/{month:02}/{day:02}".format(year=year, month=month, day=day)
    Curve_setup_dict_type_default["date"][1] = date


class Curve():
    '''This class is used to deal with curve setup dictionary, which is self.dic. All values in self.dic are strings so that it could be written to or read from a file directly. self.get() read self.dic and return a value with correct type. self.set() get a value with type, translate it into string and write the string into self.dic.'''
    def __init__(self, dic = None):
        '''If initialized with a dictionary, make a deep copy of it. Otherwise make a new dictionary and fill it with elements and default values in Curve_setup_dict_type_default.'''
        if dic != None:
            self.dic = copy.deepcopy(dic)
        else:
            self.dic = {}
            for elem in Curve_setup_dict_type_default:
                self.dic[elem] = copy.deepcopy( Curve_setup_dict_type_default[elem][1])

    def get_str(self, elem):
        '''Read self.dic, get the elemnent and translate it into string.
            If elem is a wrong element name, print out error message and return an empty string.'''
        if self.dic.has_key(elem) == False:
            print "Key Error: curve setup dictinory DO NOT have key: %s !" %str(elem)
            return ''
        else:
            if Curve_setup_dict_type_default[elem][0] == 'string':
                return self.dic[elem]
            elif Curve_setup_dict_type_default[elem][0] == 'float':
                if self.dic[elem] == None:
                    return ''
                else:
                    return str(self.dic[elem])
            elif Curve_setup_dict_type_default[elem][0] == 'bool':
                return 'True' if self.dic[elem] == True else 'False'
            elif (Curve_setup_dict_type_default[elem][0] == 'float_list') | (Curve_setup_dict_type_default[elem][0] == 'int_list'):
                result = ''
                for i in xrange(len(self.dic[elem])-1):
                    result = result + str(self.dic[elem][i]) + ','
                result = result + str(self.dic[elem][-1])
                return result

    def get_str_dic(self):
        '''This function creat a dictionary with all element being string type. It will be used for writing to file.'''
        str_dic = {}
        for elem in self.dic:
            str_dic[elem] = self.get_str(elem)
        return str_dic

    def set_value(self, elem, value, index = -1):
        '''Set element elem with value, where value could be either string or elem's type.
            If value is a string, convert it into its type first.
            If elem is a list type, while index < 0, value should be a list of numbers.
            If elem is a list type, while index > 0, value should be a single number.'''
        value_type = Curve_setup_dict_type_default[elem][0]
        if value_type == 'string':
            self.dic[elem] = str(value)
        elif value_type == 'float':
            if (value == '') | (value == None):
                self.dic[elem] = None
            else:
                self.dic[elem] = float(value)
        elif value_type == 'bool':
            if type(value) == type(''):
                self.dic[elem] = True if value == 'True' else False
            elif type(value) == type(True):
                self.dic[elem] = value
            else:
                print "Value Error: bool type could not have %s value!" %str(value)

        elif value_type == 'float_list':
            if (type(value) == type([])) & (index < 0):
                if (type(value[0]) == type(0.0)) & (len(value) == len(self.dic[elem])):
                    self.dic[elem] = value
                else:
                    print "value list type and length mismatch"
            elif ((type(value) == type(0.0)) | (type(value) == type(''))) & (index >= 0) & (index < len(self.dic[elem])):
                if value == '':
                    value = 0.0
                else:
                    value = float(value)
                self.dic[elem][index] = value
            elif (type(value) == type('')) & (index < 0):
                value_list_str = value.split(',')
                if '' in value_list_str:
                    value_list_str.remove('')
                if len(value_list_str) == len(self.dic[elem]):
                    self.dic[elem] = map(float, value_list_str)
                else:
                    print "value list length mismatch"
            else:
                print "Could not set value = %s for element %s" %(str(value), str(elem))

        elif value_type == 'int_list':
            if (type(value) == type([])) & (index < 0):
                if (type(value[0]) == type(0)) & (len(value) == len(self.dic[elem])):
                    self.dic[elem] = value
                else:
                    print "value list type and length mismatch"
            elif ((type(value) == type(0)) | (type(value) == type(''))) & (index >= 0) & (index < len(self.dic[elem])):
                if value == '':
                    value = 0
                else:
                    value = int(value)
                self.dic[elem][index] = int(value)
            elif (type(value) == type('')) & (index < 0):
                value_list_str = value.split(',')
                if '' in value_list_str:
                    value_list_str.remove('')
                if len(value_list_str) == len(self.dic[elem]):
                    self.dic[elem] = map(int, value_list_str)
                else:
                    pass
#                    print "value list length mismatch"
            else:
                print "Could not set value = %s for element %s" %(str(value), str(elem))

    def set_str_dic(self, str_dic):
        '''This function set the dictionary with values come from a external string dictionary str_dic. It will be used for reading from file.'''
        for elem in self.dic:
            if str_dic.has_key(elem):
                self.set_value(elem, str_dic[elem])
            else:
                print "Warning: element %s is not set!" %elem


    def get_data(self):
        directory = self.get_dir()
        shots = self.dic['shots']
        shots.replace(' ', '')  #remove all the spaces
#        keys = " ".join([self.dic['X'], self.dic['Y']])
#        self.data, errmsg, raw_data = qrange.qrange(directory, shots, keys)
        keys = [self.dic['X'], self.dic['Y']]
#	print 'Before qrange.'
        self.data, errmsg, raw_data = qrange.qrange_eval(directory, shots, keys)
#	print 'After qrange.'
        s = ''
        for i in range(self.data.shape[1]):
            col = self.data[:,i]
            s00 = numpy.mean(col)
            s01 = stats.sem(col)
            s02 = numpy.std(col)
            s03 = numpy.max(col) - numpy.min(col)
            s = s + "Mean = %10.6f\n" % s00
            s = s + "Std. deviation  = %10.6f\n" % s02
            s = s + "Std. Error of the mean = %10.6f\n" % s01
            s = s + "Pk-Pk = %10.6f\n" % s03
            s = s+ '\n'
        raw_data = s + raw_data
        self.dic['data_str'] = raw_data

        self.sdata = None
        if self.dic['X'] == "SEQ:shot":
            s = [ numpy.mean(self.data[:,1]), numpy.std(self.data[:,1]), stats.sem(self.data[:,1]),numpy.max(self.data[:,1]) - numpy.min(self.data[:,1]) ]
            a = []
            for val in s:
                a.append( [val for i in range(self.data[:,1].size)])
            self.sdata = numpy.c_[self.data[:,0], numpy.transpose(numpy.array(a))]
        else:
            self.sdata = statdat.statdat(self.data, 0, 1)
        return

    def get_dir(self):
        year, month, day = self.dic['date'].split('/')
        year2 = year[2:4]
        return data_dir + '/' + year + '/' + year2+month + '/' + year2+month+day + '/'

    def get_plot_func(self):
        func_name = self.dic['func']
        function = fitdict[func_name].function
        p = [ float(f) for f in self.dic['para_list']]
        data = numpy.array(self.data)
        self.plotX, self.plotY = plot_function(p, data[:,0], function)

    def get_fit(self):
        func_name = self.dic['func']
        function = fitdict[func_name].function
        p = [ float(f) for f in self.dic['para_list']]
        data = numpy.array(self.data)
        self.para_list_fit, self.error_list_fit = fit_function(p, data, function)
        self.fitX, self.fitY = plot_function(self.para_list_fit, data[:,0], function)
        self.fit_result_string = 'para' + '\t\t\t' + 'error' + '\n'
        for i, para in enumerate(self.para_list_fit):
            self.fit_result_string = self.fit_result_string + "{0:.5e}".format(para) + '\t' + "{0:.5e}".format(self.error_list_fit[i]) + '\n'
        self.dic['fit_result'] = self.fit_result_string
        return

    def get_location(self, gs):
        '''get the location in the plot panel, in unit of grid spec pixels'''
        m, n = self.dic['location']
        self.gs = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec = gs[m-1,n-1])

	self.top = self.gs.get_subplot_params().top
	self.bottom = self.gs.get_subplot_params().bottom
	self.left = self.gs.get_subplot_params().left
	self.right = self.gs.get_subplot_params().right

class Subplot():
    def __init__(self, dic = None):
        '''If initialized with a dictionary, make a deep copy of it. Otherwise make a new dictionary and fill it with elements and default values in Curve_setup_dict_type_default.'''
        if dic != None:
            self.dic = copy.deepcopy(dic)
        else:
            self.dic = dict()
            for elem in Subplot_setup_dict_type_default:
                self.dic[elem] =copy.deepcopy( Subplot_setup_dict_type_default[elem][1])

    def add_curve(self, curve = 0):
        if curve == 0:
            curve = copy.deepcopy(Curve())
        self.dic['curvelist'].append(curve)

    def del_curve(self, curve_index):
        length = len(self.dic['curvelist'])
        if (curve_index >= 0) & (curve_index < length):
            self.dic['curvelist'].pop(curve_index)
        else:
            print "index = %d is out of range of curve list, which has %d elements" %(curve_index, length)

    def get_str(self, elem):
        '''Read self.dic, get the elemnent and translate it into string.
            If elem is a wrong element name, print out error message and return an empty string.'''
        if self.dic.has_key(elem) == False:
            print "Key Error: subplot setup dictinory DO NOT have key: %s !" %str(elem)
            return ''
        else:
            elem_type = Subplot_setup_dict_type_default[elem][0]
            if elem_type == 'string':
                return self.dic[elem]
            elif elem_type == 'float':
                if self.dic[elem] == None:
                    return ''
                else:
                    return str(self.dic[elem])
            elif elem_type == 'bool':
                return 'True' if self.dic[elem] == True else 'False'

            elif (elem_type == 'float_list') | (elem_type == 'int_list'):
                result = ''
                for i in xrange(len(self.dic[elem])-1):
                    result = result + str(self.dic[elem][i]) + ','
                result = result + str(self.dic[elem][-1])
                return result

            elif elem_type == 'curve_list':
                length = len(self.dic[elem])
                result = []
                if length > 0:
                    for curve in self.dic[elem]:
                        result.append(curve.get_str_dic())
                return result

    def get_str_dic(self):
        '''This function creat a dictionary with all element being string type. It will be used for writing to file.'''
        str_dic = {}
        for elem in self.dic:
            elem_type = Subplot_setup_dict_type_default[elem][0]
            if elem_type != 'curve_list':
                str_dic[elem] = self.get_str(elem)
            else:
                curve_str_list = self.get_str(elem)
                length = len(self.dic[elem])
                if length > 0:
                    for i in xrange(length):
                        str_dic['curve %d'%(i+1)] = curve_str_list[i]
        return str_dic

    def set_value(self, elem, value, index = -1):
        '''Set element elem with value, where value could be either string or elem's type.
            If value is a string, convert it into its type first.
            If elem is a list type, while index < 0, value should be a list of numbers.
            If elem is a list type, while index > 0, value should be a single number.'''
        value_type = Subplot_setup_dict_type_default[elem][0]
        if value_type == 'string':
            self.dic[elem] = str(value)
        elif value_type == 'float':
            if (value == '') | (value == None):
                self.dic[elem] = None
            else:
                self.dic[elem] = float(value)
        elif value_type == 'bool':
            if type(value) == type(''):
                self.dic[elem] = True if value == 'True' else False
            elif type(value) == type(True):
                self.dic[elem] = value
            else:
                print "Value Error: bool type could not have %s value!" %str(value)

        elif value_type == 'int_list':
            if (type(value) == type([])) & (index < 0):
                if (type(value[0]) == type(0)) & (len(value) == len(self.dic[elem])):
                    self.dic[elem] = value
                else:
                    print "value list type and length mismatch"
            elif ((type(value) == type(0)) | (type(value) == type(''))) & (index >= 0) & (index < len(self.dic[elem])):
                if value == '':
                    value = 0
                else:
                    value = int(value)
                self.dic[elem][index] = int(value)
            elif (type(value) == type('')) & (index < 0):
                value_list_str = value.split(',')
                if '' in value_list_str:
                    value_list_str.remove('')
                if len(value_list_str) == len(self.dic[elem]):
                    self.dic[elem] = map(int, value_list_str)
                else:
                    pass
#                    print "value list length mismatch"
            else:
                print "Could not set value = %s for element %s" %(str(value), str(elem))

        elif value_type == 'curve_list':
            if (type(value) == type([])) & (index < 0):
                length = len(value)
                self.dic[elem] = []
                for i in xrange(length):
                    self.add_curve()
                    self.dic[elem][-1].set_str_dic(value[i])
            elif index >= 0:
                curve_list_length = len(self.dic[elem])
                if index >= curve_list_length:
                    while index >= curve_list_length:
                        curve_list_length = curve_list_length + 1
                        self.add_curve()
                self.dic[elem][index].set_str_dic(value)
            else:
                print "Could not set value for element %s" %str(elem)

    def set_str_dic(self, str_dic):
        '''This function set the dictionary with values come from a external string dictionary str_dic. It will be used for reading from file.'''
        for elem in self.dic:
            if elem == 'curvelist':
                for elem_str in str_dic:
                    match = elem_str.split('curve ')
                    if (len(match) == 2):
                        if (match[0] == '') & (match[1] != ''):
                            index = int(match[1]) - 1
                            self.set_value(elem, str_dic[elem_str], index)
            elif str_dic.has_key(elem):
                self.set_value(elem, str_dic[elem])
            else:
                print "Warning: element %s is not set!" %elem

    def get_name_list(self):
        name_list = []
        for curve in self.dic['curvelist']:
            name_list.append(curve.dic['name'])
        return name_list

    def get_stat(self):
        M_cur = 1
        N_cur = 1
        for curve in self.dic['curvelist']:
            if curve.dic['plotcurveB']:
                location_cur = curve.dic['location']
                if location_cur[0] > M_cur:
                    M_cur = location_cur[0]
                if location_cur[1] > N_cur:
                    N_cur = location_cur[1]
        if M_cur > self.dic['setup_grid'][0]:
	    self.M_cur = M_cur
	else:
	    self.M_cur = self.dic['setup_grid'][0]

	if N_cur > self.dic['setup_grid'][1]:
	    self.N_cur = N_cur
	else:
	    self.N_cur = self.dic['setup_grid'][1]

        for curve in self.dic['curvelist']:
            curve.set_value('curve_num', [self.M_cur, self.N_cur])

    def get_location(self, gs):
        '''get the location in the plot panel, in unit of grid spec pixels'''
        m, n = self.dic['location']
        self.get_stat()
        self.gs = gridspec.GridSpecFromSubplotSpec(self.M_cur, self.N_cur, subplot_spec = gs[m-1,n-1])
        for curve in self.dic['curvelist']:
            if curve.dic['plotcurveB']:
                curve.get_location(self.gs)

class Subplot_List():
    def __init__(self, empty = False):
        self.lst = []
        if not empty:
            self.add_subplot()
        self.current_file_dir = new_setting_dir
	self.subplot_grid = [1,1]

    def add_subplot(self, subplot = 0):
        if subplot == 0:
            subplot = copy.deepcopy(Subplot())
            subplot.add_curve()
        self.lst.append(subplot)

    def del_subplot(self, subplot_index):
        length = len(self.lst)
        if (subplot_index >= 0) & (subplot_index < length):
            self.lst.pop(subplot_index)
        else:
            print "index = %d is out of range of subplot list, which has %d elements" %(subplot_index, length)

    def get_name_list(self):
        name_list = []
        for subplot in self.lst:
            name_list.append(subplot.dic['name'])
        return name_list

    def load(self, directory = 0):
#        for subplot in self.lst:
#            del subplot
#Destruct all the elements before clean up the list
        if directory != 0:
            self.current_file_dir = directory
        self.lst = []
        self.config = ConfigObj(self.current_file_dir)
        for elem in self.config:
            subplot0 = copy.deepcopy(Subplot())
            subplot0.set_str_dic(self.config[elem])
            self.lst.append(subplot0)

    def save(self, directory = 0):
        if directory != 0:
            self.current_file_dir = directory

        self.config = ConfigObj()
        self.config.filename = self.current_file_dir
        for i, subplot in enumerate(self.lst):
            self.config[('subplot %d' %i)] = subplot.get_str_dic()
        self.config.write()

    def get_stat(self):
        '''get the number of rows and collumns for subplots'''
        M_sp = 1
        N_sp = 1
        for subplot in self.lst:
            if subplot.dic['plotsubB']:
                location_sp = subplot.dic['location']
                if location_sp[0] > M_sp:
                    M_sp = location_sp[0]
                if location_sp[1] > N_sp:
                    N_sp = location_sp[1]
        if M_sp > self.subplot_grid[0]:
	    self.M_sp = M_sp
	else:
	    self.M_sp = self.subplot_grid[0]

	if N_sp > self.subplot_grid[1]:
	    self.N_sp = N_sp
	else:
	    self.N_sp = self.subplot_grid[1]

        for subplot in self.lst:
            subplot.set_value('subplot_num', [self.M_sp, self.N_sp])

    def get_locations(self):
        '''get the locations for each subplot in the plot panel, in unit of grid spec pixels'''
        self.get_stat()
        self.gs = gridspec.GridSpec(self.M_sp, self.N_sp)
        for subplot in self.lst:
            if subplot.dic['plotsubB']:
                subplot.get_location(self.gs)


    def get_figures(self):
        '''self.figures is a list containing all curves that will be shown. self.figures = [[curve1],[curve2, curve3]...], where curve2 and curve3 are two curves in the same figure.'''
        self.get_locations()

        self.figures = []
        for subplot in self.lst:
            if subplot.dic['plotsubB']:
                for curve in subplot.dic['curvelist']:
                    if curve.dic['plotcurveB']:
                        same_figure = False
                        if len(self.figures) > 0:
                            for figure0 in  self.figures:
                                curve0 = figure0[0]
                                if (curve.top == curve0.top) & (curve.bottom == curve0.bottom) & (curve.left == curve0.left) & (curve.right == curve0.right):
                                    figure0.append(curve)
                                    same_figure = True
                        if same_figure == False:
                            self.figures.append([curve])

#        if len(self.figures) > 0:
#            for figure in self.figures:
#		i = 0
#                for curve in figure:
#                    print i, curve.dic['name']
#		    i = i+1

        return self.figures

class PlotDataCore():
    def __init__(self, parent, GUI = True):
        self.dpi = 100
        if GUI:
            self.fig = Figure((1.0, 1.0), dpi = self.dpi)
            self.canvas = FigCanvas(self, -1, self.fig)
        else:
            self.fig = None
    def show(self):
        plt.show()

def PlotFigures(subplot_list, fig = None, GUI = True):
    if fig == None:
        assert GUI == False

    if GUI:
        fig.clf()
    else:
        plt.cla()
    figures = subplot_list.get_figures()
    for figure in figures:
        legend_tuple = []
        line_tuple = []
        gs = figure[0].gs[0,0]
        if GUI:
            axes = fig.add_subplot(gs)
        else:
            plt.subplot(gs)
            axes = plt.axes()

        for index_curve, curve in enumerate(figure):
            curve.get_data()
            if len(curve.data) > 0:
                for elem in Curve_setup_dict_type_default:
                    read_code = '%s = curve.dic["%s"]' %(elem, elem)
                    exec read_code
                if matchB:
                    ec = color
                if Xl =='':
                    Xl = X
                if Yl =='':
                    Yl = Y
                legendB = False if Legend == '' else True
#                    print name, start, end, index_curve
                if curve.sdata != None and statsB:
                    sdata = curve.sdata
                    sdata = sdata[sdata[:,0].argsort()]

                    line1, = axes.plot(sdata[:,0], sdata[:,1], '-', color = color)
                    axes.fill_between(sdata[:,0], sdata[:,1] + sdata[:,2], sdata[:,1] - sdata[:,2], facecolor = color, alpha = 0.3)
                    axes.fill_between(sdata[:,0], sdata[:,1] +sdata[:,3], sdata[:,1] -sdata[:,3], facecolor = color, alpha = 0.3)
                    axes.fill_between(sdata[:,0], sdata[:,1] +sdata[:,4]/2., sdata[:,1]-sdata[:,4]/2., facecolor = color, alpha = 0.1)
                else:
                    ms_code = ''
                    if ms != None:
                        ms_code = ', ms = ms'
                    mew_code = ''
                    if mew != None:
                        mew_code = ', mew = mew'

                    plot_code = 'line1, = axes.plot(curve.data[:,0], curve.data[:,1], fmt, mec = ec, mfc = color %s %s )' %(ms_code, mew_code)
                    exec plot_code

                if plotfuncB:
                    if fitB:
                        curve.get_fit()
                        line2, = axes.plot(curve.fitX, curve.fitY)
                        Legend2 = Legend+'_fit'

                    else:
                        curve.get_plot_func()
                        line2, =axes.plot(curve.plotX, curve.plotY)
                        Legend2 = Legend+'_plot'

                if index_curve == 0:
                    axes.set_xlabel(Xl)
                    axes.set_ylabel(Yl)
                    axes.grid(gridB)

                    if xticksB == False:
                        axes.set_xticks([])

                    if yticksB == False:
                        axes.set_yticks([])

                    if logxB:
                        axes.set_xscale('log')

                    if logyB:
                        axes.set_yscale('log')

                    if (Xmin == None) & (Xmax == None) & (Ymin == None) & (Ymax == None):
                        axes.autoscale(True)
                    else:
                        axes.set_xlim(Xmin, Xmax)
                        axes.set_ylim(Ymin, Ymax)

            if legendB:
                line_tuple.append(line1)
                legend_tuple.append(Legend)
                if plotfuncB:
                    line_tuple.append(line2)
                    legend_tuple.append(Legend2)

        if legend_tuple != []:
            axes.legend(line_tuple, legend_tuple,loc = 'best')

class PlotData():
    def __init__(self, empty = False):
        # try to keep the variable name consistent with MainWindow
        self.plotpanel = PlotDataCore(None, GUI=False)
        self.subplot_list = Subplot_List(empty = empty)

    def replot(self):
        self.subplot_list.get_locations()
        PlotFigures(self.subplot_list, self.plotpanel.fig, GUI=False)

    def show(self):
        plt.show()

    def subplot_dic(self, subplot_num, curve_num):
        return self.subplot_list.lst[subplot_num].dic

    def curve_dic(self, subplot_num, curve_num):
        return self.subplot_list.lst[subplot_num].dic["curvelist"][curve_num].dic

    def fitted_expr(self, subplot_num, curve_num):
        return fill_expr(help_table[self.curve_dic(subplot_num, curve_num)['func']], self.curve_dic(subplot_num, curve_num)['fit_result'])

    def add_subplot(self, subplot = 0):
        self.subplot_list.add_subplot(subplot=subplot)
