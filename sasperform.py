import re
import bisect
import parsy as ps
import plotly.express as px
from datetime import datetime
from datetime import timedelta
from pandas import DataFrame

def noneZero(x):
    if x is None:
        return 0
    else:
        return float(x)

def dodgeGuessDate(x):
    try:
        return datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p')
    except:
        try:
            return datetime.strptime(x, '%d/%m/%Y %I:%M:%S %p')
        except:
            return datetime.strptime(x, '%d/%m/%Y %I%M %p')


_timeDelta = ps.seq(
    hours = (ps.regex(r'\d+(?=:\d+:)') << ps.string(':')).optional().map(noneZero),
    minutes = (ps.regex(r'\d+(?=:\d+)') << ps.string(':')).optional().map(noneZero),
    seconds = ps.regex(r'\d+(\.\d+)?').map(noneZero) << ps.string(' seconds').optional()
).combine_dict(timedelta)
_memory = (ps.regex(r'\d+') + ps.regex(r'\.\d+').optional() << ps.string('k')).map(float)
_timestamp =ps.regex(r'.*?(?=\s+Step)').map(lambda x: dodgeGuessDate(x))
_wsp = ps.regex(r'\s+')

_rSubmitCapture = ps.string('NOTE: Remote submit to ') >> ps.regex(r'.*(?= commencing.)') << ps.string(' commencing.')
_rSubmitExit = ps.string('NOTE: Remote submit to ') >> ps.regex(r'.*(?= complete.)') << ps.string(' complete.') 

_rSubmit = _rSubmitCapture.tag('start') | _rSubmitExit.tag('end')

_performance = ps.seq(
    process = ps.string('NOTE: ') >> ps.regex(r'.*(?=used)') << ps.string('used (Total process time):'),
    real_time = ps.regex(r'\s+real time\s+') >> _timeDelta << _wsp,
    user_cpu_time= ps.regex(r'user cpu time\s+') >> _timeDelta << _wsp,
    system_cpu_time = ps.regex(r'system cpu time\s+') >> _timeDelta << _wsp,
    memory = ps.regex(r'memory\s+') >> _memory << _wsp,
    os_memory = ps.regex(r'OS Memory\s+') >> _memory << _wsp,
    timestamp = ps.regex(r'Timestamp\s+') >> _timestamp,
    step_count = ps.regex(r'\s+Step Count\s+') >> ps.regex(r'\d+').map(int) << _wsp,
    switch_count = ps.regex(r'Switch Count\s+') >> ps.regex(r'\d+').map(int)
)

def run_performance_parse(lns, i, rsubmits):

    res = _performance.parse_partial(''.join(lns[i:i+9]))[0]

    res['logLine'] = i

    if len(rsubmits) > 0:
        rsub = _rSubmit.parse(lns[rsubmits[bisect.bisect(rsubmits,i)-1]])
        if rsub[0] == 'start':
            res['rSub'] = rsub[1]
        else:
            res['rSub'] = 'main'
    else:
        res['rSub'] = 'main'
    return res


def parse_performance_from_sas_log(logFile):

    f = logFile.decode("utf-8").split('\r\n')
    _ln = [ln for ln in f if re.match(r'.*The SAS System.*|\s*\n\s*', ln) is None]
    _indexes = [i for i, ln in enumerate(_ln) if re.match(r'.*Total process time',ln) is not None]
    _rsubmits = [i for i, ln in enumerate(_ln) if re.match(r'.*NOTE: Remote submit to',ln) is not None]
    
    return [run_performance_parse(_ln,i,_rsubmits) for i in _indexes]


def chart_log(logFile):

    res = parse_performance_from_sas_log(logFile)

    df = DataFrame(res)
    df['real_time']=df['real_time'].map(lambda x: x.total_seconds())

    stats = ['real_time']
    colors = ['red','blue','green']

    for i, stat in enumerate(stats):
        return px.line(df,x='timestamp', y=stat, color='rSub', hover_name='process',hover_data=['logLine'])



