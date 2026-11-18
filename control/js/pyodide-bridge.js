/* Group Messi - Python-first PID bridge with visible fallback if CDN fails. */
(function () {
  'use strict';
  const CDN='https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js';
  const SCRIPT_TIMEOUT_MS=9000;
  const ENGINE_TIMEOUT_MS=18000;

  function waitLimit(ms,message){
    return new Promise((_,reject)=>setTimeout(()=>reject(new Error(message)),ms));
  }
  function injectPyodide(){
    if(typeof window.loadPyodide==='function')return Promise.resolve();
    return new Promise((resolve,reject)=>{
      const script=document.createElement('script');
      const timeout=setTimeout(()=>{
        script.remove(); reject(new Error('Could not load Pyodide from jsDelivr within '+(SCRIPT_TIMEOUT_MS/1000)+' seconds.'));
      },SCRIPT_TIMEOUT_MS);
      script.src=CDN;
      script.async=true;
      script.onload=()=>{
        clearTimeout(timeout);
        if(typeof window.loadPyodide==='function') resolve();
        else reject(new Error('Pyodide script loaded but the loader was unavailable.'));
      };
      script.onerror=()=>{
        clearTimeout(timeout); reject(new Error('Pyodide CDN request failed (network, filtering, or ad blocker).'));
      };
      document.head.appendChild(script);
    });
  }
  async function initPython(status){
    await injectPyodide();
    status.textContent='Loading Python runtime…';
    const pyodide=await Promise.race([
      window.loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/'}),
      waitLimit(ENGINE_TIMEOUT_MS,'Pyodide initialization timed out')
    ]);
    const response=await Promise.race([
      fetch('py/pid_core.py', {cache:'no-store'}),
      waitLimit(9000,'Python source download timed out')
    ]);
    if(!response.ok)throw new Error('Python source py/pid_core.py: HTTP '+response.status);
    await pyodide.runPythonAsync(await response.text());
    const dispatch=pyodide.globals.get('bridge_dispatch');
    const call=(action,config)=>JSON.parse(dispatch(action, JSON.stringify(config===undefined?null:config)));
    // Test one real call before declaring the engine ready.
    const probe=call('simulate',{plant:{kind:'first',K:1,tau:1},kp:1,ki:0,kd:0,reference:1,duration:1});
    if(!probe || !probe.t || probe.t.length<3)throw new Error('Python simulation returned no time series.');
    return Object.freeze({simulate:c=>call('simulate',c),validation:()=>call('validation',null)});
  }
  async function boot(){
    const status=document.getElementById('python-status');
    if(!status)return;
    try {
      status.textContent='Loading Python/Pyodide control engine…';
      window.PIDCore=await initPython(status);
      status.textContent='Python engine ready · RK4 solver active';
      status.classList.add('ready');
      window.dispatchEvent(new Event('pid-core-ready'));
    }catch(error){
      console.warn('Group Messi HW2: Python could not start:',error);
      if(window.PIDFallback){
        window.PIDCore=window.PIDFallback;
        status.classList.add('ready');
        status.textContent='Graphs ready · JavaScript RK4 fallback active (Python/Pyodide could not load: '+error.message+'). The Python engine remains the primary implementation.';
        window.dispatchEvent(new Event('pid-core-ready'));
      }else{
        status.classList.add('failed');
        status.textContent='Unable to load the simulation: '+error.message+'. Check Console (F12) and required files.';
      }
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
