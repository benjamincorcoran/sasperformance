
import re
import parsy as ps
from datetime import datetime
from datetime import timedelta

import bisect

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
        return datetime.strptime(x, '%d/%m/%Y %I:%M:%S %p')

_timeDelta = ps.seq(
    hours = (ps.regex(r'\d+(?=:\d+:)') << ps.string(':')).optional().map(noneZero),
    minutes = (ps.regex(r'\d+(?=:\d+)') << ps.string(':')).optional().map(noneZero),
    seconds = ps.regex(r'\d+(\.\d+)?').map(noneZero) << ps.string(' seconds').optional()
).combine_dict(timedelta)
_memory = (ps.regex(r'\d+') + ps.regex(r'\.\d+').optional() << ps.string('k')).map(float)
_timestamp = ps.regex(r'.*?(?=\n)').map(lambda x: dodgeGuessDate(x))
_wsp = ps.regex(r'\s+')

_rSubmitCapture = ps.string('NOTE: Remote submit to ') >> ps.regex(r'.*(?=commencing.)') << ps.string('commencing.') + _wsp
_rSubmitExit = ps.string('NOTE: Remote submit to ') >> ps.regex(r'.*(?=complete.)') << ps.string('complete.') + _wsp

_rSubmit = _rSubmitCapture.tag('start') | _rSubmitExit.tag('end')

_performance = ps.seq(
    process = ps.string('NOTE: ') >> ps.regex(r'.*?(?=used)') << ps.string('used (Total process time):\n'),
    real_time = ps.regex(r'\s+real time\s+') >> _timeDelta << _wsp,
    user_cpu_time= ps.regex(r'user cpu time\s+') >> _timeDelta << _wsp,
    system_cpu_time = ps.regex(r'system cpu time\s+') >> _timeDelta << _wsp,
    memory = ps.regex(r'memory\s+') >> _memory << _wsp,
    os_memory = ps.regex(r'OS Memory\s+') >> _memory << _wsp,
    timestamp = ps.regex(r'Timestamp\s+') >>_timestamp << _wsp,
    step_count = ps.regex(r'Step Count\s+') >> ps.regex(r'\d+').map(int) << _wsp,
    switch_count = ps.regex(r'Switch Count\s+') >> ps.regex(r'\d+').map(int) << _wsp
)

def run_performance_parse(lns, i, rsubmits):
    res = _performance.parse(''.join(lns[i:i+8]))
    res['logLine'] = i

    rsub = _rSubmit.parse(lns[rsubmits[bisect.bisect(rsubmits,i)-1]])
    if rsub[0] == 'start':
        res['rSub'] = rsub[1]
    else:
        res['rSub'] = 'main'
    return res


def parse_performance_from_sas_log(logFile):

    with open(logFile, 'r') as f:
        _ln = [ln for ln in f.readlines() if re.match(r'.*The SAS System.*|\s*\n\s*', ln) is None]

    _indexes = [i for i, ln in enumerate(_ln) if re.match(r'.*Total process time',ln) is not None]
    _rsubmits = [i for i, ln in enumerate(_ln) if re.match(r'.*NOTE: Remote submit to',ln) is not None]


    
    
    return [run_performance_parse(_ln,i,_rsubmits) for i in _indexes]



from pandas import DataFrame
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.offline

res = parse_performance_from_sas_log('<SASLOGFILE>')



df = DataFrame(res)
df['real_time']=df['real_time'].map(lambda x: x.total_seconds())

df['creal_time']=df['real_time'].cumsum()

stats = ['real_time']
colors = ['red','blue','green']


fig = make_subplots(rows=len(stats), cols=1, shared_xaxes=True, subplot_titles=stats)
for i, stat in enumerate(stats):
    df[f'cum{stat}'] = df[stat].cumsum()
    
    _trace = px.line(df,x='timestamp', y=stat, color='rSub', hover_name='process',hover_data=['logLine'])
    plotly.offline.plot(_trace, filename = 'filename.html', auto_open=True)
    # _trace = _trace['data'][0]
    # _trace['line']['color']=colors[i]
    # fig.add_trace(_trace, row=i+1, col=1)

# _trace = px.line(df, x='timestamp', y='creal_time')
# _trace = _trace['data'][0]
# _trace['line']['color']='black'
# fig.add_trace(_trace, row=1, col=1)





