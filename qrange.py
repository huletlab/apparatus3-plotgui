import getopt, sys, configobj, numpy
 

from StringIO import StringIO

sys.path.append('L:/software/apparatus3/bin')

def parse_range(rangestr):
    shots=[] 

    l = rangestr.split(',')
    for token in l:
        if token.find(':') > -1:
            sh0 = int(token.split(':')[0])
            shf = int(token.split(':')[1])
            if shf < sh0:
                sys.stderr.write( "\n----------> RANGE ERROR: end of range is smaller than start of range\n\n")
                return
            for num in range(sh0,shf+1):
                numstr = "%04d" % num
                shots.append(numstr)
        elif token.find('-') == 0:
            l2 = token.split('-')[1:]
            for shot in l2:
                if shot in shots:
                    shots.remove(shot)
    return shots

def qrange(dir,range,keys):
    fakefile=""
    shots=parse_range(range)
    #print shots
    errmsg=''
    rawdat='#%s%s\n' % ('SEC:shot\t',keys.replace(' ','\t'))
    
    for shot in shots:
        
        
        report=dir+'report'+shot+'.INI'
        from configobj import ConfigObj
        report=ConfigObj(report)
        if report == {}:
            errmsg=errmsg + "...Report #%s does not exist in %s!\n" % (shot,dir)
            continue
        
        fakefile = fakefile + '\n'
        rawdat = rawdat + '\n%s\t\t' % shot
        line=''
        line_=''
        err=False
        for pair in keys.split(' '):
            sec = pair.split(':')[0]
            key = pair.split(':')[1]
            try:
                val = report[sec][key]
                line  = line  + val + '\t'
                fval = float(val)
                if fval > 1e5 or fval < 1e5:
                    lstr = '%.3e\t\t' % fval
                else:
                    lstr = '%.4f\t\t' % fval
                line_ = line_ + lstr
            except KeyError:
                err = True
                errstr = '...Failed to get %s:%s from #%s\n' % (sec,key,shot)
                errmsg = errmsg + errstr
        if not err:
            fakefile = fakefile + line
            rawdat = rawdat + line_
                
    a=numpy.loadtxt(StringIO(fakefile))
    print errmsg
    return a, errmsg, rawdat

if __name__ == "__main__":
    qrange('L:/data/app3/2011/1107/110725/','8888:8890','SEQ:shot CPP:nfit')
