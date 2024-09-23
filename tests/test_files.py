#%%
"""Test reading and writing files."""
from pathlib import Path

import pandas as pd

from whitespacesv import WsvDocument
from whitespacesv.line import WsvLine
ASSETS = Path(__file__).parent / "assets"


def test_table() -> None:
    path = ASSETS / "table.txt"
    csv_path = ASSETS / "table.csv"
    doc = WsvDocument.load(path)
    wsv_df = doc.to_pandas()
    wsv_str_df = doc.to_pandas(infer_types=False)
    wsv_header_false = doc.to_pandas(header=False)
    csv_header_false = pd.read_csv(csv_path, header=None)
    csv_header_false.columns = csv_header_false.columns.astype(str)

    assert wsv_header_false.equals(csv_header_false)
    csv_df = pd.read_csv(csv_path)
    assert wsv_df.equals(csv_df)
    assert wsv_str_df.equals(csv_df.astype(str))
    from_pandas = WsvDocument.from_pandas(wsv_df)
    to_pandas = from_pandas.to_pandas()
    assert wsv_df.equals(to_pandas)


def test_jagged_table() -> None:
    path = ASSETS / "jagged_table.txt"
    csv_path = ASSETS / "jagged_table.csv"
    doc = WsvDocument.load(path)
    wsv_df = doc.to_pandas()
    csv_df = pd.read_csv(csv_path)
    assert wsv_df.equals(csv_df)


def test_comment_table() -> None:
    path = ASSETS / "comment_table.txt"
    csv_path = ASSETS / "comment_table.csv"
    doc = WsvDocument.load(path)
    wsv_df = doc.to_pandas()
    csv_df = pd.read_csv(csv_path)
    assert not wsv_df.equals(csv_df)
    # without comment line
    csv_df = csv_df.iloc[:-1].astype(int)
    assert wsv_df.equals(csv_df)

def test_space_lines():
    table = '''"a b" "c d" #comment
"1 2" 3 
4 "no comment in this line"
'''
    clean = '''"a b" "c d"
"1 2" 3
4 "no comment in this line"
'''
    pretty = '''"a b"\t"c d"                    \t#comment
"1 2"\t3                        
4    \t"no comment in this line"
'''
    
    doc = WsvDocument.parse(table)
    print(repr(pretty))
    print(repr(doc.to_string("pretty")))
    assert doc.to_string() == table
    assert doc.to_string("compact") == clean
    assert doc.to_string("pretty") == pretty


def test_to_string():
    values = ['Region 10', '105', 'random', '3', '1']
    line = WsvLine(values, [None, "\t", " ", " ", " "], "test")
    doc = WsvDocument([line])
    comp = doc.to_string("compact")
    pres = doc.to_string("preserve")
    pret = doc.to_string("pretty")
    assert comp == '"Region 10" 105 random 3 1\n'
    assert pres == '"Region 10"\t105 random 3 1#test\n'
    assert pret == '"Region 10"\t105\trandom\t3\t1\t#test\n'
    
    # reparse
    comp_line = WsvLine(values, [None, " ", " ", " ", " "], None)
    pres_line = line
    pret_line = WsvLine(values, [None, "\t", "\t", "\t", "\t", "\t"], "test")
    assert WsvDocument.parse(comp).lines == [comp_line]
    assert WsvDocument.parse(pres).lines == [pres_line]
    print(repr(pret))
    print(repr(WsvDocument.parse(pret).lines))
    assert WsvDocument.parse(pret).lines == [pret_line]

# %%
