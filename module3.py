"""ENCS4380 Homework 1 — Group Messi — Module 3 (Python/Pyodide).

Mass–spring–damper, a 1 N unit-force step with zero initial state:
    m*x'' + b*x' + k*x = F(t)
    x1=x, x2=x', A=[[0,1],[-k/m,-b/m]], B=[[0],[1/m]]

All calculations, SVG paths, validation and browser event handlers are Python.
This file is also importable by CPython for numerical verification.
"""

import math
import html
from dataclasses import dataclass


@dataclass(frozen=True)
class SecondOrderModel:
    m: float
    b: float
    k: float

    def __post_init__(self):
        if self.m <= 0 or self.b < 0 or self.k <= 0:
            raise ValueError('m and k must be positive, b nonnegative')

    @property
    def wn(self):
        return math.sqrt(self.k / self.m)

    @property
    def zeta(self):
        return self.b / (2.0 * math.sqrt(self.m * self.k))

    @property
    def alpha(self):
        return self.b / (2.0 * self.m)

    @property
    def equilibrium(self):
        return 1.0 / self.k  # Fstep = 1 Newton

    @property
    def matrix_a(self):
        return ((0.0, 1.0), (-self.k / self.m, -self.b / self.m))

    @property
    def matrix_b(self):
        return (0.0, 1.0 / self.m)


def second_poles(model):
    """Eigenvalues of state matrix A, same as transfer-function poles."""
    re = -model.alpha
    discriminant = model.alpha**2 - model.wn**2
    if abs(discriminant) < 1e-11:
        return complex(re, 0), complex(re, 0)
    if discriminant < 0:
        im = math.sqrt(-discriminant)
        return complex(re, im), complex(re, -im)
    delta = math.sqrt(discriminant)
    return complex(re + delta, 0), complex(re - delta, 0)


def damping_case(model):
    if abs(model.zeta - 1.0) <= 1e-5:
        return 'Critically damped'
    return 'Underdamped' if model.zeta < 1 else 'Overdamped'


def normalized_step(t, model):
    """Normalized displacement x(t)/x∞, closed-form step response."""
    if t <= 0:
        return 0.0
    z = model.zeta
    wn = model.wn
    a = model.alpha
    if abs(z - 1.0) < 1e-5:
        return 1.0 - math.exp(-wn * t) * (1.0 + wn * t)
    if z < 1:
        wd = wn * math.sqrt(1 - z*z)
        return 1.0 - math.exp(-a*t) * (math.cos(wd*t) + (a/wd)*math.sin(wd*t))
    d = wn * math.sqrt(z*z - 1)
    r1, r2 = -a + d, -a - d
    return 1.0 - (r2*math.exp(r1*t) - r1*math.exp(r2*t)) / (r2-r1)


def step_displacement(t, model):
    return model.equilibrium * normalized_step(t, model)


def step_velocity(t, model):
    """Physical velocity in m/s, derivative of the closed-form displacement."""
    if t <= 0:
        return 0.0
    wn, a, z = model.wn, model.alpha, model.zeta
    scale = model.equilibrium
    if abs(z - 1.0) < 1e-5:
        return scale * wn*wn*t*math.exp(-wn*t)
    if z < 1:
        wd = wn * math.sqrt(1-z*z)
        return scale * (wn*wn/wd) * math.exp(-a*t) * math.sin(wd*t)
    d = wn * math.sqrt(z*z-1)
    r1, r2 = -a+d, -a-d
    return scale * r1*r2 * (math.exp(r2*t)-math.exp(r1*t)) / (r2-r1)


def theoretical_overshoot_percent(zeta):
    return 100*math.exp(-math.pi*zeta/math.sqrt(1-zeta*zeta)) if 0 <= zeta < 1 else 0.0


def duration_for(model):
    """Show enough time for decay without making the graph excessively wide."""
    if model.zeta < 1:
        if model.alpha > 0:
            period = 2*math.pi/(model.wn*math.sqrt(1-model.zeta**2))
            T = max(10, 6/model.alpha, 2.7*period)
        else:
            T = 16.0
    else:
        slow = max(1e-9, -max(p.real for p in second_poles(model)))
        T = max(10, 7/slow)
    return min(75.0, max(10.0, T))


def sampled_step(model, duration, count=2400):
    return [(duration*i/count, normalized_step(duration*i/count, model)) for i in range(count+1)]


def first_crossing(points, level):
    for (ta, ya), (tb, yb) in zip(points, points[1:]):
        if ya < level <= yb:
            return ta + (tb-ta) * (level-ya)/(yb-ya)
    return None


def response_metrics(points, duration, model):
    """Estimate rise (10-90%), first peak, overshoot and 2% settling from curve."""
    t10, t90 = first_crossing(points, 0.1), first_crossing(points, 0.9)
    rise = t90-t10 if t10 is not None and t90 is not None else None
    largest_t, largest_value = max(points, key=lambda item: item[1])
    overshoot = max(0.0, (largest_value-1.0)*100)
    peak_time = largest_t if overshoot > 0.015 and 0 < largest_t < duration else None
    last_outside = max((index for index,(_,v) in enumerate(points) if abs(v-1.0)>0.02), default=-1)
    settling = None if last_outside == len(points)-1 else points[last_outside+1][0]
    return dict(rise=rise, peak=peak_time, overshoot=overshoot, settling=settling)


def format_poles(eigenvalues):
    a,b = eigenvalues
    signed = lambda x: f'{x:.3f}'.replace('-', '−')
    if abs(a.imag)>1e-7:
        return f'{signed(a.real)} ± j{abs(a.imag):.3f}'
    if abs(a.real-b.real) < 1e-7:
        return f'{signed(a.real)} (double pole)'
    return f'{signed(a.real)}, {signed(b.real)}'


def second_validation_results():
    """Reference lecture cases 4/5/6; independent of user slider positions."""
    actual4 = theoretical_overshoot_percent(.5)
    actual5 = theoretical_overshoot_percent(1.0)
    model6 = SecondOrderModel(1, 2, 4)
    actual6 = second_poles(model6)
    pass4 = abs(actual4-16.3) <= .1
    pass5 = actual5 == 0
    pass6 = (abs(model6.zeta-.5)<1e-10 and abs(model6.wn-2)<1e-10 and
             abs(actual6[0].real+1)<1e-10 and abs(abs(actual6[0].imag)-math.sqrt(3))<1e-10)
    return {'test4': (actual4, pass4), 'test5': (actual5, pass5),
            'test6': (format_poles(actual6), pass6)}


# ----- SVG graphs, generated in Python (no chart library required) -----

COLORS = {'selected':'#0879b9', 'under':'#7bbce2', 'critical':'#d1a02c',
          'over':'#637991', 'axis':'#64839b', 'gold':'#d1a02c'}


def fmt(v, digits=2):
    return f'{v:.{digits}f}'


def svg_line(x1, y1, x2, y2, css='chart-grid', extra=''):
    return (f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" '
            f'y2="{y2:.2f}" class="{css}" {extra}/>')


def svg_label(x, y, value, css='chart-axis', anchor='middle'):
    return (f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" '
            f'class="{css}">{html.escape(str(value))}</text>')


def svg_curve(points, xscale, yscale):
    return ' '.join(('M' if i==0 else 'L') + f'{xscale(x):.2f},{yscale(y):.2f}'
                    for i,(x,y) in enumerate(points))


def draw_step_graph(model, duration, data=None):
    data = data if data is not None else sampled_step(model, duration)
    w,h,left,right,top,bottom = 760,335,66,23,21,46
    pw,ph=w-left-right,h-top-bottom
    references=[]
    for damping,color in ((.5,COLORS['under']), (1,COLORS['critical']), (1.6,COLORS['over'])):
        ref=SecondOrderModel(model.m,2*damping*math.sqrt(model.m*model.k),model.k)
        references.append((color, sampled_step(ref,duration,380)))
    maxvalue=max([v for _,v in data] + [v for _,pts in references for _,v in pts])
    ymax=max(1.25, min(2, maxvalue + .12))
    x=lambda t:left+pw*t/duration
    y=lambda val:top+ph*(1-val/ymax)
    result=[]
    for i in range(6):
        t=duration*i/5
        val=ymax*i/5
        result.append(svg_line(x(t),top,x(t),h-bottom))
        result.append(svg_label(x(t),h-bottom+22,f'{t:.1f}'))
        result.append(svg_line(left,y(val),w-right,y(val)))
        result.append(svg_label(left-12,y(val)+4,f'{val:.2f}',anchor='end'))
    result.append(svg_label(left,13,'NORMALIZED DISPLACEMENT','chart-axis-label','start'))
    result.append(svg_line(left,y(1),w-right,y(1),extra='stroke="#d1a02c" stroke-width="2" stroke-dasharray="6 5"'))
    result.append(svg_label(w-right-5,y(1)-8,'Final value = 1','chart-axis-label','end'))
    for color, pts in references:
        result.append(f'<path d="{svg_curve(pts,x,y)}" fill="none" stroke="{color}" '
                      f'stroke-width="2.2" stroke-dasharray="6 5"/>')
    # Fewer points in chart than metrics: smooth while keeping Pyodide responsive.
    selected=data[::max(1,len(data)//850)]
    if selected[-1] != data[-1]: selected.append(data[-1])
    result.append(f'<path d="{svg_curve(selected,x,y)}" fill="none" stroke="{COLORS["selected"]}" '
                  'stroke-width="3.8" stroke-linejoin="round" stroke-linecap="round"/>')
    result.append(f'<circle cx="{x(0):.2f}" cy="{y(0):.2f}" r="5" fill="{COLORS["selected"]}" stroke="white" stroke-width="2"/>')
    met=response_metrics(data,duration,model)
    if met['peak'] is not None:
        tp=met['peak']
        result.append(f'<circle cx="{x(tp):.2f}" cy="{y(normalized_step(tp,model)):.2f}" r="5" '
                      f'fill="{COLORS["gold"]}" stroke="white" stroke-width="2"/>')
        result.append(svg_label(x(tp)+9,y(normalized_step(tp,model))-12,'Peak','chart-marker-label','start'))
    return ''.join(result)


def draw_poles_graph(model):
    roots=second_poles(model)
    w,h,left,right,top,bottom=540,310,58,24,25,42
    re_values=[abs(p.real) for p in roots]
    left_limit=-max(2.5,max(re_values)*1.3)
    right_limit=max(.7,-left_limit*.16)
    imlimit=max(1.8,max(abs(p.imag) for p in roots)*1.4)
    pw,ph=w-left-right,h-top-bottom
    x=lambda real:left+pw*(real-left_limit)/(right_limit-left_limit)
    y=lambda imag:top+ph*(imlimit-imag)/(2*imlimit)
    out=[]
    for i in range(6):
        val=left_limit+(right_limit-left_limit)*i/5
        out.append(svg_line(x(val),top,x(val),h-bottom))
        out.append(svg_label(x(val),h-bottom+20,f'{val:.1f}'))
    for i in range(-2,3):
        val=imlimit*i/2
        out.append(svg_line(left,y(val),w-right,y(val)))
        out.append(svg_label(left-8,y(val)+4,f'{val:.1f}',anchor='end'))
    out.append(svg_line(x(0),top,x(0),h-bottom,extra='stroke="#64839b" stroke-width="1.8"'))
    out.append(svg_line(left,y(0),w-right,y(0),extra='stroke="#64839b" stroke-width="1.8"'))
    out.append(svg_label(w-right,h-8,'REAL(s)','chart-axis-label','end'))
    out.append(svg_label(left,14,'IMAGINARY(s)','chart-axis-label','start'))
    for i,root in enumerate(roots):
        xp,yp=x(root.real),y(root.imag)
        if i==1 and abs(roots[0]-root)<1e-7:
            xp+=3  # signal a repeated pole, keeping both visible
        out.append(svg_line(xp-6,yp-6,xp+6,yp+6,extra=f'stroke="{COLORS["selected"]}" stroke-width="3"'))
        out.append(svg_line(xp-6,yp+6,xp+6,yp-6,extra=f'stroke="{COLORS["selected"]}" stroke-width="3"'))
    return ''.join(out)


def draw_phase_graph(model, duration):
    points=[(step_displacement(duration*i/780,model),step_velocity(duration*i/780,model)) for i in range(781)]
    xmin=min([x for x,_ in points]+[0,model.equilibrium]); xmax=max([x for x,_ in points]+[model.equilibrium])
    ymin=min([y for _,y in points]+[0]); ymax=max([y for _,y in points]+[0])
    dx=max(.01,xmax-xmin);dy=max(.01,ymax-ymin)
    xmin-=.13*dx;xmax+=.13*dx;ymin-=.16*dy;ymax+=.16*dy
    w,h,left,right,top,bottom=540,310,64,22,27,47
    pw,ph=w-left-right,h-top-bottom
    x=lambda d:left+pw*(d-xmin)/(xmax-xmin)
    y=lambda v:top+ph*(ymax-v)/(ymax-ymin)
    pieces=[]
    for i in range(6):
        d=xmin+(xmax-xmin)*i/5
        pieces.append(svg_line(x(d),top,x(d),h-bottom))
        pieces.append(svg_label(x(d),h-bottom+20,f'{d:.2f}'))
    for i in range(5):
        v=ymin+(ymax-ymin)*i/4
        pieces.append(svg_line(left,y(v),w-right,y(v)))
        pieces.append(svg_label(left-9,y(v)+4,f'{v:.2f}',anchor='end'))
    pieces.append(svg_line(left,y(0),w-right,y(0),extra='stroke="#64839b" stroke-width="1"'))
    pieces.append(f'<path d="{svg_curve(points,x,y)}" fill="none" stroke="{COLORS["selected"]}" '
                  'stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
    pieces.append(f'<circle cx="{x(0):.2f}" cy="{y(0):.2f}" r="5" fill="{COLORS["gold"]}" stroke="white" stroke-width="2"/>')
    pieces.append(f'<circle cx="{x(model.equilibrium):.2f}" cy="{y(0):.2f}" r="6" fill="white" '
                  f'stroke="{COLORS["selected"]}" stroke-width="2.5"/>')
    pieces.append(svg_label(w-right,h-9,'DISPLACEMENT x₁ (m)','chart-axis-label','end'))
    pieces.append(svg_label(left,13,'VELOCITY x₂ (m/s)','chart-axis-label','start'))
    return ''.join(pieces)


# ----- Pyodide DOM integration -----

def start_second_order_browser_app():
    from js import document
    from pyodide.ffi import create_proxy

    proxies=[]

    def el(node_id):
        return document.getElementById(node_id)

    def label(node_id,text):
        el(node_id).textContent=str(text)

    def on(node,event,handler):
        proxy=create_proxy(handler)
        proxies.append(proxy)
        node.addEventListener(event,proxy)

    def render(event=None):
        model=SecondOrderModel(float(el('so-m').value),float(el('so-b').value),float(el('so-k').value))
        duration=duration_for(model)
        data=sampled_step(model,duration)
        metric=response_metrics(data,duration,model)
        label('so-m-value', f'{model.m:.2f} kg')
        label('so-b-value', f'{model.b:.2f} N·s/m')
        label('so-k-value', f'{model.k:.2f} N/m')
        label('so-zeta', f'{model.zeta:.3f}')
        label('so-wn', f'{model.wn:.3f} rad/s')
        label('so-case', damping_case(model))
        label('so-rise', f'{metric["rise"]:.2f} s' if metric['rise'] is not None else '—')
        label('so-peak', f'{metric["peak"]:.2f} s' if metric['peak'] is not None else '—')
        label('so-overshoot',f'{metric["overshoot"]:.1f}%')
        label('so-settle',f'{metric["settling"]:.2f} s' if metric['settling'] is not None else f'> {duration:.0f} s')
        label('so-A21', f'{-model.k/model.m:.3f}'.replace('-', '−'))
        label('so-A22', f'{-model.b/model.m:.3f}'.replace('-', '−'))
        label('so-B2', f'{1/model.m:.3f}')
        label('so-eigen', format_poles(second_poles(model)))
        label('so-poles-text',f'System poles = eigenvalues of A: {format_poles(second_poles(model))}')
        el('so-step-chart').innerHTML=draw_step_graph(model,duration,data)
        el('so-poles-chart').innerHTML=draw_poles_graph(model)
        el('so-phase-chart').innerHTML=draw_phase_graph(model,duration)
        label('so-step-caption',f'The response approaches {model.equilibrium:.3f} m. Reference curves use the same mass and stiffness.')
        for node in document.querySelectorAll('[data-zeta]'):
            active=abs(float(node.dataset.zeta)-model.zeta)<.002
            node.classList.toggle('active',active)
            node.setAttribute('aria-pressed','true' if active else 'false')

    def preset(event):
        node=event.currentTarget
        target=float(node.dataset.zeta)
        m,k=float(el('so-m').value),float(el('so-k').value)
        el('so-b').value=str(2*target*math.sqrt(m*k))
        render()

    def reset(event=None):
        el('so-m').value='1';el('so-b').value='2';el('so-k').value='4'
        for radio in document.querySelectorAll('input[name="so-prediction"]'):
            radio.checked=False
        feedback=el('so-predict-feedback')
        feedback.className='prediction-feedback'
        feedback.textContent='Select an answer to test your prediction.'
        render()

    def predict(event=None):
        selected=document.querySelector('input[name="so-prediction"]:checked')
        feedback=el('so-predict-feedback')
        if selected is None:
            feedback.className='prediction-feedback try-again'
            feedback.textContent='Choose a prediction first.'
            return
        m,k=float(el('so-m').value),float(el('so-k').value)
        # A controlled example: set zeta to .5 then increase it to .85
        el('so-b').value=str(2*.85*math.sqrt(m*k))
        render()
        if selected.value=='less':
            feedback.className='prediction-feedback success'
            feedback.textContent='✓ Correct. Increasing damping reduces overshoot. The selected response now has ζ = 0.85.'
        else:
            feedback.className='prediction-feedback try-again'
            feedback.textContent='Not quite: increasing damping reduces overshoot. The current response has ζ = 0.85.'

    def validate():
        results=second_validation_results()
        passed=0
        for name,(value,passflag) in results.items():
            text=(f'{value:.2f}%' if name in ('test4','test5') else f'ζ=0.5; ωn=2; poles {value}')
            label('so-'+name,text)
            status=el('so-'+name+'-status')
            status.textContent='PASS' if passflag else 'FAIL'
            status.className='test-pass' if passflag else 'test-fail'
            passed+=int(passflag)
        label('so-validation-status',f'{passed} / 3 PASS')

    for node_id in ('so-m','so-b','so-k'):
        on(el(node_id),'input',render)
    for node in document.querySelectorAll('[data-zeta]'):
        on(node,'click',preset)
    on(el('so-reset'),'click',reset)
    on(el('so-predict-check'),'click',predict)
    validate()
    render()
    for node_id in ('so-m','so-b','so-k','so-reset','so-predict-check'):
        el(node_id).disabled=False
    for node in document.querySelectorAll('[data-zeta]'):
        node.disabled=False


if __name__ == '__main__':
    start_second_order_browser_app()
