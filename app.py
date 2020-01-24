import panel as pn
from sasperform import *
from plotly.graph_objs import Figure
pn.extension('plotly')

TEMPLATE = """
{% extends base %}

<!-- goes in body -->
{% block postamble %}
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
{% endblock %}

<!-- goes in body -->
{% block contents %}
<h1>SAS Performance Reviewer</h1>
<p>This is a panel app built to review SAS logs extract performance metrics</p>
    
<div id="fileInput">
    {{embed(roots.file_input)}} {{embed(roots.button)}}
</div>

{{embed(roots.text)}}

{{embed(roots.fig)}}



{% endblock %}
"""

def b(event):
    if fileInput.value is not None:
        fig.object = chart_log(fileInput.value)
    else:
        print('Loading...')
    

text = pn.pane.Str()
fileInput = pn.widgets.FileInput()


button = pn.widgets.Button(name='Parse', button_type='primary')
button.on_click(b)

fig = pn.pane.Plotly()


tmpl = pn.Template(TEMPLATE)
tmpl.add_panel("file_input", fileInput)
tmpl.add_panel("button",button)
tmpl.add_panel("fig",fig)


tmpl.add_panel('text',text)


tmpl.servable()

