/* ENCS4380 Homework 2 — interface, plotting, predictions, motor experiment and code generation. */
(function () {
  'use strict';
  let C; // Python PID engine adapter, set after Pyodide is ready
  const byId = id => document.getElementById(id);
  const num = id => Number(byId(id).value);
  const get = id => byId(id).value;
  const set = (id, val) => {byId(id).value=val; refreshOutput(id);};
  const fmt = (v, n=2) => Number.isFinite(v) ? v.toFixed(n) : '—';
  const escapeHTML = s => String(s).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const palette={response:'#19c6ff',setpoint:'#d9a22c',sensor:'#7d93b8',control:'#ff3b55',limit:'#ff4d63'};
  let raf=null, last={};

  function refreshOutput(id) {
    const output=byId('v-'+id);
    if (output) output.textContent=String(Number(byId(id).value).toFixed(Math.min(3,(String(byId(id).step).split('.')[1]||'').length))).replace(/\.0+$/,'');
  }
  function metricTile(label, value, unit='') {
    return `<div class="metric"><strong>${value}${unit}</strong><span>${escapeHTML(label)}</span></div>`;
  }
  function renderMetrics(id, trace, custom) {
    const m=trace.metrics;
    const items=custom||[
      ['Rise time (10–90%)',fmt(m.riseTime,2),' s'],
      ['Overshoot',fmt(m.overshoot,1),'%'],
      ['Settling (2%)',fmt(m.settlingTime,2),' s'],
      ['Steady error',fmt(m.steadyError,2),'%']
    ];
    byId(id).innerHTML=items.map(([name,v,unit])=>metricTile(name,v,unit)).join('');
  }
  function series(name, values, color, stair=false) {return {name,values,color,stair};}
  function plot(id, trace, plotted, options={}) {
    const canvas=byId(id), box=canvas.getBoundingClientRect();
    const width=Math.max(275,Math.round(box.width||650));
    // Fixed logical plot heights: canvas.height is the backing-store height,
    // and must never be reused as CSS height on subsequent slider updates.
    const height=({'p1-output':270,'p1-u':190,'p2-output':310})[id] || 260;
    canvas.style.width='100%';
    canvas.style.height=height+'px';
    const dpr=Math.min(window.devicePixelRatio||1,2);
    canvas.width=Math.round(width*dpr); canvas.height=Math.round(height*dpr);
    const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);
    const pad={left:49,right:14,top:34,bottom:33};
    const plotW=width-pad.left-pad.right, plotH=height-pad.top-pad.bottom;
    ctx.clearRect(0,0,width,height);ctx.fillStyle='#0a1019';ctx.fillRect(0,0,width,height);
    const time=trace.t, endTime=Math.max(0.1,time[time.length-1]);
    let rangeY=plotted.reduce((ar,s)=>{
      for(let i=0;i<s.values.length;i++){
        const y=s.values[i];if(Number.isFinite(y)) {ar[0]=Math.min(ar[0],y);ar[1]=Math.max(ar[1],y);}
      }return ar;
    },[Infinity,-Infinity]);
    let minY=options.minY!==undefined?options.minY:rangeY[0];
    let maxY=options.maxY!==undefined?options.maxY:rangeY[1];
    if(!Number.isFinite(minY)||!Number.isFinite(maxY)){minY=0;maxY=1;}
    if(options.minY===undefined)minY=Math.min(0,minY);
    if(maxY-minY<.001)maxY=minY+1;
    if(options.maxY===undefined)maxY+=(maxY-minY)*.09;
    if(options.minY===undefined&&minY<0)minY-=(maxY-minY)*.05;
    const xp=t=>pad.left+t/endTime*plotW;
    const yp=y=>pad.top+plotH-(y-minY)/(maxY-minY)*plotH;
    ctx.font='11px system-ui'; ctx.lineWidth=1;ctx.textAlign='right';ctx.textBaseline='middle';
    for(let i=0;i<=4;i++){
      const y=pad.top+plotH*i/4;
      ctx.beginPath();ctx.strokeStyle='#27394d';ctx.moveTo(pad.left,y);ctx.lineTo(width-pad.right,y);ctx.stroke();
      ctx.fillStyle='#8fa5b9';ctx.fillText(fmt(maxY-(maxY-minY)*i/4, maxY-minY<4?2:1),pad.left-7,y);
    }
    ctx.textAlign='center';ctx.textBaseline='top';
    for(let i=0;i<=5;i++){
      const x=pad.left+plotW*i/5;
      ctx.beginPath();ctx.strokeStyle='#1c2a3b';ctx.moveTo(x,pad.top);ctx.lineTo(x,pad.top+plotH);ctx.stroke();
      ctx.fillStyle='#879cb1';ctx.fillText(fmt(endTime*i/5,1),x,height-25);
    }
    ctx.save();ctx.beginPath();ctx.rect(pad.left,pad.top,plotW,plotH);ctx.clip();
    for(const s of plotted){
      ctx.strokeStyle=s.color;ctx.lineWidth=s.name==='Setpoint'?1.7:2.1;
      if(s.name==='Setpoint')ctx.setLineDash([7,4]);else ctx.setLineDash([]);
      ctx.beginPath(); const stride=Math.max(1,Math.ceil(s.values.length/2200));
      for(let i=0;i<s.values.length;i+=stride){
        const xv=xp(time[i]),yv=yp(s.values[i]);
        if(i===0)ctx.moveTo(xv,yv);
        else if(s.stair){ctx.lineTo(xv,yp(s.values[Math.max(0,i-stride)]));ctx.lineTo(xv,yv);}
        else ctx.lineTo(xv,yv);
      }
      const lastIdx=s.values.length-1;ctx.lineTo(xp(time[lastIdx]),yp(s.values[lastIdx]));ctx.stroke();
    }
    ctx.restore();ctx.setLineDash([]);
    let lx=pad.left,ly=10;ctx.textAlign='left';ctx.textBaseline='middle';ctx.font='10px system-ui';
    for(const s of plotted){
      const textWidth=ctx.measureText(s.name).width;const needed=textWidth+27;
      if(lx+needed>width-10){lx=pad.left;ly+=14;}
      ctx.strokeStyle=s.color;ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(lx,ly);ctx.lineTo(lx+13,ly);ctx.stroke();
      ctx.fillStyle='#bed2e1';ctx.fillText(s.name,lx+17,ly);lx+=needed+10;
    }
  }
  function clearAnswer(id){byId(id).textContent='';}
  function modelP1(extra={}) {
    const kind=get('p1-kind');
    return C.simulate({plant:{kind,K:num('p1-k'),tau:num('p1-tau'),zeta:num('p1-zeta'),wn:num('p1-wn')},kp:num('p1-kp'),ki:num('p1-ki'),kd:num('p1-kd'),reference:num('p1-r'),mode:'continuous',uMin:0,uMax:100,duration:kind==='first'?Math.max(12,num('p1-tau')*9):15,dt:.006,antiWindup:true,...extra});
  }
  function updateP1(){
    document.querySelectorAll('.p1-first').forEach(el=>el.classList.toggle('hidden',get('p1-kind')!=='first'));
    document.querySelectorAll('.p1-second').forEach(el=>el.classList.toggle('hidden',get('p1-kind')!=='second'));
    const t=modelP1();last.p1=t;
    plot('p1-output',t,[series('Setpoint',t.reference,palette.setpoint),series('Actual y',t.y,palette.response)]);
    plot('p1-u',t,[series('PWM command',t.control,palette.control)],{minY:0,maxY:100});
    renderMetrics('p1-metrics',t);
  }
  function modelP2(extra={}) {
    return C.simulate({plant:{kind:'first',K:1,tau:1},kp:num('p2-kp'),ki:num('p2-ki'),kd:num('p2-kd'),reference:1,sensorTau:num('p2-sensor'),mode:'continuous',uMin:0,uMax:100,duration:24,dt:.005,...extra});
  }
  function updateP2(){
    const t=modelP2();last.p2=t;
    plot('p2-output',t,[series('Setpoint',t.reference,palette.setpoint),series('True y',t.y,palette.response),series('Reported sensor ym',t.sensor,palette.sensor)]);
    const maxDiff=Math.max(...t.y.map((v,i)=>Math.abs(v-t.sensor[i])));
    renderMetrics('p2-metrics',t,[['Overshoot',fmt(t.metrics.overshoot,1),'%'],['Peak |y−ym|',fmt(maxDiff,2),''],['Settling (2%)',fmt(t.metrics.settlingTime,2),' s'],['Steady error',fmt(t.metrics.steadyError,2),'%']]);
    byId('p2-explanation').textContent=`The PID uses ym (sensor reading) while the graph shows both ym and the true y. Here the maximum lag mismatch is ${fmt(maxDiff,2)} output units. Larger sensor delay can reduce phase margin and increase overshoot or oscillation; the outcome depends on the gains.`;
  }
  function validation(){
    const checks=C.validation();
    byId('validation-body').innerHTML=checks.map(r=>`<tr><td>${escapeHTML(r.name)}</td><td>${escapeHTML(r.expected)}</td><td>${escapeHTML(r.actual)}</td><td class="${r.pass?'ok':'bad'}">${r.pass?'PASS':'FAIL'}</td></tr>`).join('');
  }
  function compare(pred,actual,valueA,valueB,unit){
    const ok=pred===actual;
    return `${ok?'✓ Correct.':'Not quite.'} Actual: ${unit} changed from ${fmt(valueA,3)} to ${fmt(valueB,3)}. ${actual==='same'?'There was almost no change.':actual==='up'||actual==='longer'?'It increased.':'It decreased.'}`;
  }
  function direction(a,b,less='shorter',more='longer'){
    if(a===null||b===null)return 'unavailable';
    if(Math.abs(b-a)<Math.max(.001,Math.abs(a)*.025))return 'same';
    return b<a?less:more;
  }
  function updateAll(){raf=null;try{updateP1();updateP2();}catch(e){console.error('Checkpoint simulation error',e);byId('python-status').textContent='Simulation error: '+e.message;}}
  function schedule(){if(!raf)raf=requestAnimationFrame(updateAll);}
  function wire(){
    document.querySelectorAll('input[type=range]').forEach(el=>{
      refreshOutput(el.id);
      el.addEventListener('input',()=>{refreshOutput(el.id);schedule();clearAnswer(el.id.slice(0,2)+'-answer');});
    });
    byId('p1-kind').addEventListener('change',()=>{schedule();clearAnswer('p1-answer');});
    byId('p1-p-only').onclick=()=>{set('p1-kind','first');set('p1-k',1);set('p1-tau',1);set('p1-kp',9);set('p1-ki',0);set('p1-kd',0);set('p1-r',1);clearAnswer('p1-answer');schedule();};
    byId('p1-pi').onclick=()=>{set('p1-kind','first');set('p1-k',1);set('p1-tau',1);set('p1-kp',1);set('p1-ki',1);set('p1-kd',0);set('p1-r',1);clearAnswer('p1-answer');schedule();};
    byId('p1-reset').onclick=()=>{set('p1-kind','first');set('p1-k',1);set('p1-tau',1);set('p1-kp',3);set('p1-ki',1);set('p1-kd',.1);set('p1-r',1);clearAnswer('p1-answer');schedule();};
    byId('p2-fast').onclick=()=>{set('p2-sensor',0);schedule();};
    byId('p2-slow').onclick=()=>{set('p2-sensor',1);schedule();};
    byId('p2-osc').onclick=()=>{set('p2-kp',10);set('p2-ki',2);set('p2-kd',0);set('p2-sensor',1.4);schedule();};
    byId('p1-check').onclick=()=>{
      const a=modelP1(),b=modelP1({kp:Math.max(.001,num('p1-kp')*1.2)});
      const actual=direction(a.metrics.riseTime,b.metrics.riseTime);
      byId('p1-answer').textContent=actual==='unavailable'?'Rise time was not measurable for one of the trials. Try different gains.':compare(get('p1-pred'),actual,a.metrics.riseTime,b.metrics.riseTime,'Rise time (s)');
    };
    byId('p2-check').onclick=()=>{
      const a=modelP2(),b=modelP2({sensorTau:Math.min(2,num('p2-sensor')+.2)});
      const actual=direction(a.metrics.overshoot,b.metrics.overshoot,'down','up');
      byId('p2-answer').textContent=actual==='unavailable'?'Overshoot is undefined here; try different gains.':compare(get('p2-pred'),actual,a.metrics.overshoot,b.metrics.overshoot,'Overshoot (%)');
    };
    let lastWidth=window.innerWidth;window.addEventListener('resize',()=>{if(Math.abs(window.innerWidth-lastWidth)>3){lastWidth=window.innerWidth;schedule();}});
  }
  window.addEventListener('pid-core-ready',()=>{C=window.PIDCore;wire();validation();updateAll();});
})();
