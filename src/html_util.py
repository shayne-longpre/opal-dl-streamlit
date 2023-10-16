import json
import numpy as np
import pandas as pd

import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
import streamlit.components.v1 as components

def compose_html_component(data_summary, target_file, vars_to_files, height = None):
    #two options to control height: either set height argument in function declaration or set const vh below and un-comment vh use in sunburst diagram
    h = height if height != None else 600
    html_dir = "html"

    sketch = '<div id="container"></div>'
    sketch += '<script type="module" src="https://d3js.org/d3.v5.min.js"></script>'
    sketch += '<script type="module" src="https://cdn.jsdelivr.net/npm/d3@7/+esm"></script>'
    # sketch += '<script type="module" src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.6.0/p5.js"></script>'
    # sketch += '<script type="module" src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.6.0/addons/p5.sound.min.js"></script>'
    # sketch += '<script type="module" src="https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm"></script>'
    sketch += '<script type="module" src="https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6.11/+esm"></script>'
    
    # For worldmap
    sketch += '<script src="https://unpkg.com/topojson@3"></script>'
    sketch += '<script src="https://unpkg.com/topojson-client@3"></script>'
    # For style
    sketch += '<style>' + open(f"{html_dir}/style.css", 'r', encoding='utf-8').read() + '</style>'


    sketch += '<script>'
    sketch += "const dataSummary = " + json.dumps(data_summary) + "\n"
    # sketch += "const dataSummary = " + open(f"{html_dir}/data_summary.json", 'r', encoding='utf-8').read() + "\n"
    if vars_to_files:
        for varname, fpath in vars_to_files.items():
            sketch += f"const {varname} = " + open(fpath, 'r', encoding='utf-8').read() + "\n"
        sketch += f"const vh = {h} " + "\n" # set height of viewport

    sketch += open(f"{html_dir}/helpers.js", 'r', encoding='utf-8').read() + "\n"
    sketch += open(f"{html_dir}/{target_file}", 'r', encoding='utf-8').read()
    sketch += '</script>'
    components.html(sketch, height=h)




# def insert_plot_viz1():
#     sketch = '<div id="container"></div>'
#     sketch += '<script type="module" src="https://d3js.org/d3.v5.min.js"></script>'
#     sketch += '<script type="module" src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.6.0/p5.js"></script>'
#     sketch += '<script type="module" src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.6.0/addons/p5.sound.min.js"></script>'
#     sketch += '<script type="module" src="https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm"></script>'
#     # sketch += '<link rel="stylesheet" type="text/css" href="style.css">'
#     sketch += '<style>' + open("static2/style.css", 'r', encoding='utf-8').read() + '</style>'
#     # sketch += '<script type="module"> import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";</script>'
    
#     sketch += '<script>'
#     sketch += "const JSONDATA = " + open("static2/data_summary.json", 'r', encoding='utf-8').read() + "\n"
#     sketch += open("static2/plot.js", 'r', encoding='utf-8').read()
#     sketch += '</script>'
#     components.html(sketch, height=800, scrolling=True)


def insert_plot_viz2():
    sketch = '<div id="container"></div>'
    sketch += '<script type="module" src="https://d3js.org/d3.v5.min.js"></script>'
    sketch += '<script type="module" src="https://cdn.jsdelivr.net/npm/d3@7/+esm"></script>'
    sketch += '<script type="module" src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.6.0/p5.js"></script>'
    sketch += '<script type="module" src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.6.0/addons/p5.sound.min.js"></script>'
    sketch += '<script type="module" src="https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm"></script>'

    sketch += '<script src="https://unpkg.com/topojson@3"></script>'
    sketch += '<script src="https://unpkg.com/topojson-client@3"></script>'

    sketch += '<style>' + open("static2/style.css", 'r', encoding='utf-8').read() + '</style>'
    # sketch += '<script type="module"> import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6/+esm";</script>'
    
    sketch += '<script>'
    sketch += "const JSONDATA = " + open("static2/data_summary.json", 'r', encoding='utf-8').read() + "\n"

    sketch += "const world = " + open("static2/countries-50m.json", 'r', encoding='utf-8').read() + "\n"
    sketch += "const countryCodes = " + open("static2/country-codes.json", 'r', encoding='utf-8').read() + "\n"
    sketch += "const langCodes = " + open("static2/language-codes.json", 'r', encoding='utf-8').read() + "\n"
    sketch += "const countryCodeToLangCodes = " + open("static2/country-code-to-language-codes.json", 'r', encoding='utf-8').read() + "\n"

    sketch += open("static2/worldmap.js", 'r', encoding='utf-8').read()
    sketch += '</script>'
    components.html(sketch, height=800, scrolling=True)


def setup_table(selected_data):

    # selected_data = data[_PRESENT_COLS]

    custom_css = {".ag-header-cell-text": {"font-size": "12px", 'text-overflow': 'revert;', 'font-weight': 700},
                ".ag-theme-streamlit": {'transform': "scale(0.8)", "transform-origin": '0 0'}}
    gb = GridOptionsBuilder.from_dataframe(selected_data, axis=1)
    gb.configure_default_column(cellStyle={'color': 'black', 'font-size': '12px'}, suppressMenu=True, wrapHeaderText=True, autoHeaderHeight=True)
    gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
    gb.configure_side_bar() #Add a sidebar
    # gb.configure_selection('single', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
    gridOptions = gb.build()

    # https://streamlit-aggrid.readthedocs.io/en/docs/AgGrid.html
    # Highlight Rows: https://discuss.streamlit.io/t/aggrid-is-there-a-way-to-color-a-row-based-on-a-column-value/20750/2
    grid_response = AgGrid(
        selected_data,
        gridOptions=gridOptions,
        custom_css=custom_css, allow_unsafe_jscode=True,
        data_return_mode='AS_INPUT', 
        # update_mode='MODEL_CHANGED', 
        update_mode='NO_UPDATE', 
        # update_mode='SELECTION_CHANGED',
        fit_columns_on_grid_load=False,
        theme='material', # streamlit, material
        height=2400, 
        width='100%',
        # reload_data=True
    )

    # resp_data = grid_response['data']
    # selected_rows = grid_response['selected_rows']

    # if selected_rows:

    #     row_index = selected_rows[0]["rowIndex"]
    #     selected_info = resp_data.iloc[row_index]