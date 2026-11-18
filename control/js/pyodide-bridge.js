/* Lightweight browser ↔ Python bridge. PID calculations are in py/pid_core.py. */
(function () {
  'use strict';
  async function boot() {
    const status=document.getElementById('python-status');
    try {
      if (typeof loadPyodide!=='function') throw Error('Pyodide loader was not found; check your internet connection.');
      status.textContent='Initializing Python control engine (Pyodide)…';
      const pyodide = await loadPyodide();
      const response=await fetch('py/pid_core.py');
      if (!response.ok) throw Error('Failed to load Python model: HTTP '+response.status);
      await pyodide.runPythonAsync(await response.text());
      const dispatch=pyodide.globals.get('bridge_dispatch');
      const call=(action,arg)=>JSON.parse(dispatch(action,JSON.stringify(arg===undefined?null:arg)));
      window.PIDCore=Object.freeze({
        simulate:config=>call('simulate',config),
        validation:()=>call('validation',null)
      });
      status.textContent='Python engine ready · RK4 numerical solver active';
      status.classList.add('ready');
      window.dispatchEvent(new Event('pid-core-ready'));
    } catch (error) {
      console.error('HW2 Python engine failed:',error);
      status.classList.add('failed');
      status.textContent='Unable to initialize the Python engine. Serve the site over HTTP / GitHub Pages and ensure the Pyodide CDN is reachable. Details: '+error.message;
    }
  }
  document.addEventListener('DOMContentLoaded',boot,{once:true});
})();
