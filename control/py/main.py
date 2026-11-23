"""
main.py - starts the Control section: builds every module's controls, then
draws a module when its tab is opened (Plotly needs a visible div).
"""

from js import window
from pyodide.ffi import create_proxy

import p1_playground
import p2_sensor
import p3_digital
import p4_challenge
import my_system
import validation

MODULES = {
    "p1": p1_playground,
    "p2": p2_sensor,
    "p3": p3_digital,
    "p4": p4_challenge,
    "my": my_system,
    "val": validation,
}
_drawn = set()
_keep = []


def render_tab(name):
    mod = MODULES.get(name)
    if mod is None:
        return
    if name not in _drawn:
        _drawn.add(name)
        mod.render()


def start():
    for mod in MODULES.values():
        mod.init()
    proxy = create_proxy(render_tab)
    _keep.append(proxy)
    window.renderTab = proxy
    window.pyReady()
