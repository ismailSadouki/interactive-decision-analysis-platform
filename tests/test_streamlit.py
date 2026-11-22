"""Page execution smoke tests plus interchange without a running browser."""
from io import BytesIO
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from decision_engine.matrix import ModelError
from streamlit_ui.common import parse_table

ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_entry():
    app=AppTest.from_file(str(ROOT / "app.py"),default_timeout=30).run()
    assert not list(app.exception)
    assert app.title[0].value == "DecisionLab"


@pytest.mark.parametrize("module,function", [
    ("views","concepts"),("views","matrix_page"),("views","certainty_page"),
    ("views","uncertainty_page"),("views","risk_page"),("views","comparison"),
    ("advanced","tree_page"),("advanced","bayes_page"),("advanced","examples_page"),
])
def test_streamlit_views(module,function):
    script=f'''import streamlit as st
from streamlit_ui import {module}
from streamlit_ui.common import bootstrap
bootstrap()
{module}.{function}()
'''
    app=AppTest.from_string(script,default_timeout=30).run()
    assert not list(app.exception), [e.message for e in app.exception]
    assert len(app.title) == 1


def test_csv_interchange():
    class Upload(BytesIO):
        name = "example.csv"
        @property
        def size(self):
            return len(self.getbuffer())
    m = parse_table(Upload((ROOT/"examples"/"investment.csv").read_bytes()), "profit")
    assert len(m.alternatives) == len(m.states) == 3
    assert m.values[2] == (-115,410,760)
    with pytest.raises(ModelError):
        parse_table(Upload(b"Alternative,S,S\nTest,1,2"),"cost")


def test_xlsx_import():
    from openpyxl import Workbook
    class Upload(BytesIO):
        name="example.xlsx"
        @property
        def size(self):
            return len(self.getbuffer())
    file=Upload()
    wb=Workbook()
    ws=wb.active
    ws.append(["Alternative","حالة أ","حالة ب"])
    ws.append(["بديل أ",4,-1])
    wb.save(file)
    file.seek(0)
    m = parse_table(file,"cost")
    assert m.states == ("حالة أ","حالة ب")
    assert m.values == ((4,-1),)
