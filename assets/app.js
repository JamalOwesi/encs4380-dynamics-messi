/* ENCS4380 – Module 1: First-order dynamic characteristics.
   Closed-form response; no dependencies, server, or internet required. */
(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const gainSlider = $('gain');
  const tauSlider = $('tau');
  const timeEnd = 30;                    // seconds; fixed for visual comparison
  const A = 1;                          // step height = 1, ramp slope = 1 unit/s
  const svgNS = 'http://www.w3.org/2000/svg';
  const chartGeom = {w: 760, h: 315, l: 66, r: 26, t: 20, b: 42};
  const logGeom = {w: 760, h: 292, l: 74, r: 26, t: 22, b: 42};

  const fixed = (v, digits=2) => v.toFixed(digits);
  const step = (t, K, tau) => K * A * (-Math.expm1(-t / tau));
  const ramp = (t, K, tau) => K * A * (t - tau * (-Math.expm1(-t / tau)));
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const ns = (tag, attrs={}, text=null) => {
    const el = document.createElementNS(svgNS, tag);
    for (const [name, value] of Object.entries(attrs)) el.setAttribute(name, value);
    if (text !== null) el.textContent = text;
    return el;
  };
  const append = (root, tag, attrs, text) => root.appendChild(ns(tag, attrs, text));
  const pathFor = (fn, count=350) => {
    const pts=[];
    for(let i=0;i<=count;i++) {const [x,y]=fn(timeEnd*i/count); if(Number.isFinite(x)&&Number.isFinite(y)) pts.push(`${i?'L':'M'}${fixed(x,2)},${fixed(y,2)}`);}
    return pts.join(' ');
  };
  const chartFrame = (svg, g, yMax, ticks, yFormat) => {
    const {w,h,l,r,t,b}=g;
    const x = (tm) => l + (w-l-r)*tm/timeEnd;
    const y = (val) => t + (h-t-b)*(1-val/yMax);
    svg.replaceChildren();
    for(let j=0;j<=6;j++){
      const tm=j*5, px=x(tm);
      append(svg,'line',{x1:px,x2:px,y1:t,y2:h-b,class:'chart-grid'});
      append(svg,'text',{x:px,y:h-b+21,'text-anchor':'middle',class:'chart-axis'},String(tm));
    }
    for(let j=0;j<=ticks;j++){
      const val=yMax*j/ticks, py=y(val);
      append(svg,'line',{x1:l,x2:w-r,y1:py,y2:py,class:'chart-grid'+(j===0?' major':'')});
      append(svg,'text',{x:l-11,y:py+4,'text-anchor':'end',class:'chart-axis'},yFormat(val));
    }
    append(svg,'text',{x:l-4,y:12,class:'chart-axis-label'},'OUTPUT (units)');
    return {x,y};
  };
  const setText = (id, txt) => {$(id).textContent=txt;};

  function drawResponse(K,tau,kind){
    const svg=$('response-chart');
    const model = kind==='step'?step:ramp;
    const ideal = (t) => K*A*(kind==='step'?1:t);
    const lastIdeal=ideal(timeEnd);
    const yMax=kind==='step'?Math.max(1,Math.ceil(K*1.25*2)/2):Math.max(5,Math.ceil(lastIdeal*1.12/5)*5);
    const {x,y}=chartFrame(svg,chartGeom,yMax,5,(v)=>Number.isInteger(v)?String(v):fixed(v,1));
    append(svg,'path',{d:pathFor(t=>[x(t),y(ideal(t))]),class:'chart-ideal'});
    append(svg,'path',{d:pathFor(t=>[x(t),y(model(t,K,tau))]),class:'chart-output'});
    if(kind==='step'){
      for(const [tm,label,color] of [[tau,'63.2% · τ','#1685c5'],[3*tau,'95.0% · 3τ','#d9a22c']]){
        const px=x(tm),py=y(step(tm,K,tau));
        append(svg,'line',{x1:px,x2:px,y1:chartGeom.t,y2:chartGeom.h-chartGeom.b,class:'chart-mark'});
        append(svg,'circle',{cx:px,cy:py,r:6,class:'chart-marker-circle',fill:color});
        const anchor=tm>timeEnd-7?'end':'start';
        const textX=tm>timeEnd-7?px-9:px+9;
        const textY=py<43?py+20:py-13;
        append(svg,'text',{x:textX,y:textY,'text-anchor':anchor,class:'chart-marker-label'},label);
      }
    } else {
      // Demonstrate the finite-time vertical error near the right side of the plot.
      const tm=27,px=x(tm),idealY=y(ideal(tm)),realY=y(ramp(tm,K,tau));
      append(svg,'line',{x1:px,x2:px,y1:idealY,y2:realY,stroke:'#d9a22c','stroke-width':2});
      append(svg,'circle',{cx:px,cy:realY,r:5,fill:'#1685c5',stroke:'#ffffff','stroke-width':2});
      append(svg,'text',{x:px-8,y:realY+19,'text-anchor':'end',class:'chart-marker-label'},'lag');
    }
  }

  function drawError(tau){
    // For both step and ramp, the transient error fraction is exp(-t/τ).
    // For ramp it is (steady-state error - current error)/steady-state error.
    const svg=$('error-chart'),g=logGeom,{w,h,l,r,t,b}=g;
    const x=(tm)=>l+(w-l-r)*tm/timeEnd;
    const y=(lnE)=>t+(h-t-b)*(-lnE)/Math.log(10000);
    svg.replaceChildren();
    for(let j=0;j<=6;j++){
      const tm=j*5,px=x(tm);
      append(svg,'line',{x1:px,x2:px,y1:t,y2:h-b,class:'chart-grid'});
      append(svg,'text',{x:px,y:h-b+22,'text-anchor':'middle',class:'chart-axis'},String(tm));
    }
    for(let j=0;j<=4;j++){
      const py=t+(h-t-b)*j/4;
      append(svg,'line',{x1:l,x2:w-r,y1:py,y2:py,class:'chart-grid'});
      append(svg,'text',{x:l-11,y:py+4,'text-anchor':'end',class:'chart-axis'},j===0?'1':`10⁻${j}`);
    }
    append(svg,'text',{x:l,y:12,class:'chart-axis-label'},'ERROR FRACTION (log scale)');
    // Stop plotting at 10^-4 rather than falsely clamping the curve along the bottom.
    const maxTime=Math.min(timeEnd,tau*Math.log(10000));
    const d=[];
    for(let i=0;i<=250;i++){
      const tm=maxTime*i/250;
      d.push(`${i?'L':'M'}${fixed(x(tm),2)},${fixed(y(-tm/tau),2)}`);
    }
    append(svg,'path',{d:d.join(' '),class:'chart-output'});
    append(svg,'circle',{cx:x(0),cy:y(0),r:5,fill:'#1685c5'});
  }

  function updateValidation(K,tau){
    const r1=step(tau,K,tau)/(K*A)*100;
    const r2=step(3*tau,K,tau)/(K*A)*100;
    const pass1=Math.abs(r1-63.2)<=0.05;
    const pass2=Math.abs(r2-95.0)<=0.05;
    setText('test-one-result',`${fixed(r1)}% of KA`);
    setText('test-two-result',`${fixed(r2)}% of KA`);
    for(const [i,pass] of [[1,pass1],[2,pass2]]){
      const el=$(`test-${i===1?'one':'two'}-status`);
      el.textContent=pass?'PASS':'FAIL';
      el.className=pass?'test-pass':'test-fail';
    }
    const n=Number(pass1)+Number(pass2);
    setText('validation-status',`${n} / 2 PASSED`);
  }

  function render(){
    const K=Number(gainSlider.value),tau=Number(tauSlider.value);
    const kind=document.querySelector('input[name="signal"]:checked').value;
    setText('gain-readout',fixed(K,1));
    setText('tau-readout',`${fixed(tau,1)} s`);
    setText('response-subtitle',kind==='step'?'· step input':'· ramp input');
    drawResponse(K,tau,kind);
    drawError(tau);
    setText('slope-readout',`Slope = −${fixed(1/tau,3)} s⁻¹`);
    if(kind==='step'){
      setText('metric-one-title','AT t = τ');
      setText('metric-one',`${fixed(step(tau,K,tau)/(K*A)*100,1)}%`);
      setText('metric-one-detail','of the final step value');
      setText('metric-two-title','AT t = 3τ');
      setText('metric-two',`${fixed(step(3*tau,K,tau)/(K*A)*100,1)}%`);
      setText('metric-two-detail','of the final step value');
      setText('metric-three-title','FINAL VALUE');
      setText('metric-three',fixed(K*A,2));
      setText('metric-three-detail','K × step amplitude');
      setText('response-caption','At τ: 63.2% of KA. At 3τ: 95.0% of KA.');
    }else{
      setText('metric-one-title','RAMP TIME LAG');
      setText('metric-one',`${fixed(tau,1)} s`);
      setText('metric-one-detail','approaches τ at steady state');
      setText('metric-two-title','STEADY-STATE ERROR');
      setText('metric-two',fixed(K*A*tau,2));
      setText('metric-two-detail','vertical error = KAτ');
      setText('metric-three-title','ERROR AT 30 s');
      setText('metric-three',fixed(K*A*tau*(-Math.expm1(-timeEnd/tau)),2));
      setText('metric-three-detail','Kx(30) − y(30)');
      setText('response-caption','The ideal ramp is KAt. At steady state the output trails by τ seconds.');
    }
    updateValidation(K,tau);
  }

  gainSlider.addEventListener('input',render);
  tauSlider.addEventListener('input',render);
  document.querySelectorAll('input[name="signal"]').forEach(el=>el.addEventListener('change',render));
  $('reset').addEventListener('click',()=>{
    gainSlider.value='1';tauSlider.value='4';$('input-step').checked=true;
    document.querySelectorAll('input[name="prediction"]').forEach(el=>el.checked=false);
    $('prediction-feedback').className='prediction-feedback';
    setText('prediction-feedback','Choose an answer to test your intuition.');
    render();
  });
  $('check-prediction').addEventListener('click',()=>{
    const choice=document.querySelector('input[name="prediction"]:checked');
    const feedback=$('prediction-feedback');
    if(!choice){feedback.className='prediction-feedback try-again';feedback.textContent='Choose one of the three predictions first.';return;}
    const original=Number(tauSlider.value);
    const increased=clamp(Math.round((original+1.5)*10)/10,0.5,8);
    // If τ is at the maximum, lower to 6.5 first, then increase to 8.
    const newTau=increased>original?increased:8;
    if(original>=8){tauSlider.value='6.5';render();}
    tauSlider.value=String(newTau);
    render();
    if(choice.value==='slower'){
      feedback.className='prediction-feedback success';
      feedback.textContent='✓ Correct! Increasing τ makes the step response slower. The final step value KA stays the same.';
    }else{
      feedback.className='prediction-feedback try-again';
      feedback.textContent='Not quite. The right answer is “more slowly.” A larger τ delays the response but does not change KA.';
    }
  });
  render();
})();
