/* Secondary browser-only RK4 engine: used ONLY if Pyodide cannot load.
   Python /py/pid_core.py is the primary implementation for HW2. */
/* ENCS4380 Homework 2 — numerical PID simulation engine.
 * Plant states integrated with fourth-order Runge-Kutta (RK4).
 * No web service, framework, or plot library required.
 * PID continuous mode: derivative on measurement, avoids setpoint kick.
 * PID digital mode: positional formula from HW2, derivative on error.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.PIDFallback = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const finite = n => Number.isFinite(n) ? n : 0;
  const defaults = {
    plant: {kind: 'first', K: 1, tau: 1, zeta: .5, wn: 3},
    kp: 2, ki: 1, kd: 0, reference: 1, sensorTau: 0,
    uMin: 0, uMax: 100, duration: 15, dt: .005, mode: 'continuous',
    sampleTime: .05, antiWindup: true
  };
  function numericalModel(opts = {}) {
    const c = {...defaults, ...opts, plant: {...defaults.plant, ...(opts.plant || {})}};
    if (!(c.plant.K > 0)) throw Error('Plant gain K must be positive.');
    if (c.plant.kind === 'first' && !(c.plant.tau > 0)) throw Error('Plant τ must be positive.');
    if (c.plant.kind === 'second' && (!(c.plant.wn > 0) || !(c.plant.zeta >= 0))) throw Error('ωn must be positive and ζ nonnegative.');
    if (!(c.uMin < c.uMax)) throw Error('Control limits must be ordered.');
    if (c.mode === 'digital' && !(c.sampleTime > 0)) throw Error('Ts must be positive.');
    c.duration = clamp(c.duration, .5, 45);
    c.dt = clamp(c.dt, .0002, .03);
    c.kp = Math.max(0, finite(c.kp)); c.ki = Math.max(0, finite(c.ki));
    c.kd = Math.max(0, finite(c.kd)); c.reference = finite(c.reference);
    c.sensorTau = Math.max(0, finite(c.sensorTau));
    return c;
  }
  function derivatives(s, u, c) {
    let dy, dv;
    if (c.plant.kind === 'second') {
      dy = s.v;
      dv = c.plant.wn * c.plant.wn * (c.plant.K * u - s.y) - 2 * c.plant.zeta * c.plant.wn * s.v;
    } else {
      dy = (c.plant.K * u - s.y) / c.plant.tau;
      dv = 0;
    }
    return {y: dy, v: dv, sensor: c.sensorTau > 0 ? (s.y - s.sensor) / c.sensorTau : 0};
  }
  function add(s, a, scale) {
    return {y: s.y + scale * a.y, v: s.v + scale * a.v, sensor: s.sensor + scale * a.sensor};
  }
  function rk4(s, u, h, c) {
    const k1 = derivatives(s, u, c);
    const k2 = derivatives(add(s, k1, h / 2), u, c);
    const k3 = derivatives(add(s, k2, h / 2), u, c);
    const k4 = derivatives(add(s, k3, h), u, c);
    const x = {
      y: s.y + h * (k1.y + 2*k2.y + 2*k3.y + k4.y) / 6,
      v: s.v + h * (k1.v + 2*k2.v + 2*k3.v + k4.v) / 6,
      sensor: s.sensor + h * (k1.sensor + 2*k2.sensor + 2*k3.sensor + k4.sensor) / 6
    };
    if (c.sensorTau <= 0) x.sensor = x.y;
    return x;
  }
  function holdPID(c, e, previousError, integral, dt) {
    const derivative = c.kd * (e - previousError) / dt; // HW2 Eq. (P3)
    const candidateI = integral + c.ki * dt * e;
    const rawCandidate = c.kp * e + candidateI + derivative;
    const beyondHigh = rawCandidate > c.uMax && e > 0;
    const beyondLow  = rawCandidate < c.uMin && e < 0;
    const nextI = c.antiWindup && (beyondHigh || beyondLow) ? integral : candidateI;
    const raw = c.kp * e + nextI + derivative;
    return {u: clamp(raw, c.uMin, c.uMax), integral: nextI, raw};
  }
  function continuousPID(c, e, previousMeasurement, measurement, integral, dt) {
    // D-on-measurement avoids derivative kick on setpoint changes in the playground.
    const derivative = -c.kd * (measurement - previousMeasurement) / dt;
    const candidateI = integral + c.ki * dt * e;
    const rawCandidate = c.kp * e + candidateI + derivative;
    const beyondHigh = rawCandidate > c.uMax && e > 0;
    const beyondLow  = rawCandidate < c.uMin && e < 0;
    const nextI = c.antiWindup && (beyondHigh || beyondLow) ? integral : candidateI;
    const raw = c.kp * e + nextI + derivative;
    return {u: clamp(raw, c.uMin, c.uMax), integral: nextI, raw};
  }
  function simulate(options) {
    const c = numericalModel(options);
    let state = {y: 0, v: 0, sensor: 0}, integral = 0, prevMeasurement = 0, prevError = 0, u = 0;
    const t = [], y = [], m = [], control = [], ref = [], raw = [];
    const save = (time, rawU) => {
      t.push(time); y.push(state.y); m.push(c.sensorTau <= 0 ? state.y : state.sensor);
      control.push(u); ref.push(c.reference); raw.push(rawU);
    };
    const shortestTime = c.plant.kind === 'first' ? c.plant.tau : 1 / c.plant.wn;
    const sensorResolution = c.sensorTau > 0 ? c.sensorTau / 12 : 1;
    const baseH = Math.min(c.dt, shortestTime / 12, sensorResolution);
    if (c.mode === 'digital') {
      // Update control only once each Ts, hold it constant between ticks (zero-order hold).
      // RK4 integrates the plant at smaller substeps; no approximation of the plant by steps of Ts.
      let time = 0;
      while (time < c.duration - 1e-10) {
        const window = Math.min(c.sampleTime, c.duration - time);
        const measurement = c.sensorTau <= 0 ? state.y : state.sensor;
        const e = c.reference - measurement;
        const result = holdPID(c, e, prevError, integral, c.sampleTime);
        u = result.u; integral = result.integral; prevError = e;
        const n = Math.max(1, Math.ceil(window / baseH));
        const h = window / n;
        save(time, result.raw);
        for (let j = 0; j < n; j++) {
          state = rk4(state, u, h, c);
          time += h;
          if (j < n - 1 && (j+1) % Math.max(1, Math.floor(n/10)) === 0) save(time, result.raw);
          if (Math.abs(state.y) > 1e7 || !Number.isFinite(state.y)) break;
        }
        if (Math.abs(state.y) > 1e7 || !Number.isFinite(state.y)) break;
      }
      save(Math.min(c.duration, time), u);
    } else {
      const steps = Math.ceil(c.duration / baseH);
      const h = c.duration / steps;
      for (let i = 0; i <= steps; i++) {
        const time = i*h;
        const measurement = c.sensorTau <= 0 ? state.y : state.sensor;
        const e = c.reference - measurement;
        const result = continuousPID(c, e, prevMeasurement, measurement, integral, h);
        u = result.u; integral = result.integral; prevMeasurement = measurement;
        save(time, result.raw);
        if (i !== steps) state = rk4(state, u, h, c);
        if (Math.abs(state.y) > 1e7 || !Number.isFinite(state.y)) break;
      }
    }
    const metrics = measure({t,y,control}, c.reference, c.uMax);
    return {t, y, sensor:m, control, reference:ref, raw, metrics, config:c};
  }
  function interpolateCrossing(times, values, level) {
    for (let i = 1; i < values.length; i++) {
      if (values[i-1] < level && values[i] >= level) {
        const dy = values[i] - values[i-1];
        return times[i-1] + (dy === 0 ? 0 : (level-values[i-1])/dy)*(times[i]-times[i-1]);
      }
    }
    return null;
  }
  function measure(trace, target, uMax=100) {
    const {t, y, control} = trace;
    const n = y.length;
    if (n < 3) return {riseTime:null,overshoot:null,settlingTime:null,steadyError:null,iae:null, peakU:null,unstable:true};
    const tail = Math.max(4, Math.floor(n*.04));
    const finalY = y.slice(-tail).reduce((a,b)=>a+b,0)/tail;
    const maxY = Math.max(...y), minY = Math.min(...y);
    const peakU = Math.max(...control);
    const amplitude = Math.abs(finalY-y[0]);
    const direction = finalY >= y[0] ? 1 : -1;
    const oriented = y.map(v => direction*(v-y[0]));
    const t10 = interpolateCrossing(t, oriented, .1*amplitude);
    const t90 = interpolateCrossing(t, oriented, .9*amplitude);
    const riseTime = t10 === null || t90 === null ? null : t90 - t10;
    const overshoot = amplitude < 1e-7 ? null : 100*Math.max(0,direction*(direction===1?maxY:minY)-direction*finalY)/amplitude;
    const band = .02 * Math.max(Math.abs(finalY), .01*Math.abs(target), 1e-6);
    let lastBad = -1;
    for (let i = 0; i < n; i++) if (Math.abs(y[i]-finalY) > band) lastBad=i;
    const settlingTime = lastBad >= n-1 ? null : lastBad < 0 ? 0 : t[lastBad+1];
    let iae=0;
    for (let i=1;i<n;i++) iae += .5*(Math.abs(target-y[i])+Math.abs(target-y[i-1]))*(t[i]-t[i-1]);
    const referenceScale = Math.max(Math.abs(target),1e-9);
    const steadyError=100*(target-finalY)/referenceScale;
    const unstable = !Number.isFinite(finalY) || Math.abs(finalY)>1e5 || Math.abs(steadyError)>10000;
    return {riseTime,overshoot,settlingTime,steadyError,iae,peakU,finalY,maxY, unstable, actuatorSaturated:control.some(u=>u>=uMax-1e-8)};
  }
  function dampingForPI(K,tau,kp,ki) {
    if (!(K>0&&tau>0&&ki>0)) return null;
    const wn = Math.sqrt(K*ki/tau);
    return {wn,zeta:(1+K*kp)/(2*tau*wn)};
  }
  function validation() {
    const c={plant:{kind:'first',K:1,tau:1},reference:1,uMin:0,uMax:100,dt:.001,duration:16};
    const proportional=simulate({...c,kp:9,ki:0,kd:0});
    const pTau=interpolateCrossing(proportional.t,proportional.y,.9*(1-Math.exp(-1)));
    const pError=proportional.metrics.steadyError;
    const pi=simulate({...c,kp:1,ki:1,kd:0});
    const poles=dampingForPI(1,1,1,1);
    const alt=simulate({...c,kp:2,ki:1,kd:0,duration:22});
    return [
      {name:'P only: Kp=9, closed-loop τ',expected:'0.100 s',actual:pTau===null?'—':pTau.toFixed(4)+' s',pass:pTau!==null&&Math.abs(pTau-.1)<.004},
      {name:'P only: Kp=9, step steady-state error',expected:'10.0%',actual:pError.toFixed(3)+'%',pass:Math.abs(pError-10)<.1},
      {name:'PI: Kp=1, Ki=1, ωn and ζ',expected:'1.000 rad/s, 1.000',actual:`${poles.wn.toFixed(3)} rad/s, ${poles.zeta.toFixed(3)}; OS=${pi.metrics.overshoot.toFixed(2)}%`,pass:Math.abs(poles.wn-1)<.001&&Math.abs(poles.zeta-1)<.001&&pi.metrics.overshoot<.5},
      {name:'PI: zero step steady-state error',expected:'≈ 0%',actual:alt.metrics.steadyError.toFixed(4)+'%',pass:Math.abs(alt.metrics.steadyError)<.1}
    ];
  }
  return {simulate,measure,validation,dampingForPI,interpolateCrossing,clamp};
});
