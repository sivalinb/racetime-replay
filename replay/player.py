"""One video clock drives charts and route in an isolated local HTML component."""

import base64
import json
from pathlib import Path


def player_html(video_path: str | Path, aligned, events: list[dict]) -> str:
    """Build a sandboxed player whose video clock drives local charts and route."""
    media = base64.b64encode(Path(video_path).read_bytes()).decode()
    rows = json.loads(
        aligned[["video_s", "speed_mps", "heart_rate_bpm", "latitude", "longitude"]].to_json(
            orient="records"
        )
    )
    payload = json.dumps({"rows": rows, "events": events}).replace("<", "\\u003c")
    return """<!doctype html><html><head><style>
*{box-sizing:border-box}body{margin:0;background:#0d2027;color:#e4efed;font:14px system-ui}
.wrap{padding:18px;border:1px solid #26434a;border-radius:16px}.grid{display:grid;grid-template-columns:1.7fr 1fr;gap:16px}
video{width:100%;max-height:330px;background:#051015;border-radius:10px}canvas{width:100%;border-radius:8px;background:#102a32}
h3{font-size:13px;font-weight:500;color:#9cbab9;margin:0 0 8px}.numbers{display:flex;gap:28px;margin:12px 0}.n{font-size:24px;color:#faf6ee}
small{color:#9cbab9}.events{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}button{padding:8px 10px;color:#dcebe8;border:1px solid #49656c;background:#193840;border-radius:20px;cursor:pointer}button:hover{background:#31535a}
input{width:100%;accent-color:#f0ae6e}.caption{font-size:12px;color:#97b2b3;margin-top:8px}@media(max-width:650px){.grid{grid-template-columns:1fr}.wrap{padding:10px}}
</style></head><body><div class="wrap"><div class="grid"><div><video id="video" controls preload="metadata" src="data:video/mp4;base64,MEDIA"></video>
<div class="numbers"><div><small>VIDEO TIME</small><div class="n" id="time">0:00</div></div><div><small>SPEED · M/S</small><div class="n" id="speed">—</div></div><div><small>HEART RATE · BPM</small><div class="n" id="hr">—</div></div></div>
<input aria-label="Seek synchronized replay" type="range" id="seek" min="0" step="0.1" value="0"><div class="caption">Scrub the video or click a signal chart. Missing samples stay blank.</div></div>
<div><h3>WORKOUT SIGNALS</h3><canvas aria-label="Synchronized speed and heart rate chart" id="chart" width="420" height="195"></canvas><h3 style="margin-top:16px">ROUTE SHAPE · NO EXTERNAL MAP SERVICE</h3><canvas aria-label="Route position" id="map" width="420" height="130"></canvas></div></div><div class="events" id="events"></div><div class="caption">Candidates require review. Visual motion does not establish running speed or a medical cause.</div></div>
<script>const data=PAYLOAD, rows=data.rows, v=document.getElementById('video'), seek=document.getElementById('seek');
const duration=rows.length?rows[rows.length-1].video_s:1;seek.max=duration;
function fmt(t){return Math.floor(t/60)+':'+String(Math.floor(t%60)).padStart(2,'0')}
function draw(t){let row=rows.reduce((a,b)=>Math.abs(b.video_s-t)<Math.abs(a.video_s-t)?b:a,rows[0]);
document.getElementById('time').textContent=fmt(t);document.getElementById('speed').textContent=row.speed_mps==null?'—':row.speed_mps.toFixed(1);document.getElementById('hr').textContent=row.heart_rate_bpm==null?'—':Math.round(row.heart_rate_bpm);seek.value=t;
let c=document.getElementById('chart'),ctx=c.getContext('2d');ctx.clearRect(0,0,c.width,c.height);
function line(key,color,top,h,max){ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();let pen=false;for(let r of rows){if(r[key]==null){pen=false;continue}let x=12+r.video_s/duration*396,y=top+h-Math.min(r[key]/max,1)*h;if(pen)ctx.lineTo(x,y);else ctx.moveTo(x,y);pen=true}ctx.stroke()}
line('speed_mps','#65d0ba',25,60,Math.max(5,...rows.map(r=>r.speed_mps||0)));line('heart_rate_bpm','#f0ae6e',110,60,220);
ctx.fillStyle='#a5c0c3';ctx.font='12px system-ui';ctx.fillText('Speed',12,18);ctx.fillText('Heart rate',12,103);ctx.strokeStyle='#f7f4ed';let x=12+t/duration*396;ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,195);ctx.stroke();
let m=document.getElementById('map'),mc=m.getContext('2d');mc.clearRect(0,0,420,130);let geo=rows.filter(r=>r.latitude!=null&&r.longitude!=null);if(!geo.length){mc.fillStyle='#a5c0c3';mc.fillText('No route samples',20,60);return}
let xs=geo.map(r=>r.longitude),ys=geo.map(r=>r.latitude),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
let project=r=>[20+(r.longitude-xmin)/(xmax-xmin||1)*380,110-(r.latitude-ymin)/(ymax-ymin||1)*90];mc.strokeStyle='#557d80';mc.lineWidth=3;mc.beginPath();geo.forEach((r,i)=>{let[x,y]=project(r);if(i)mc.lineTo(x,y);else mc.moveTo(x,y)});mc.stroke();if(row.latitude!=null&&row.longitude!=null){let[x,y]=project(row);mc.fillStyle='#f0ae6e';mc.beginPath();mc.arc(x,y,6,0,7);mc.fill()}}
v.ontimeupdate=()=>draw(v.currentTime);seek.oninput=()=>{v.currentTime=Number(seek.value);draw(v.currentTime)};document.getElementById('chart').onclick=e=>{let rect=e.target.getBoundingClientRect();v.currentTime=Math.max(0,Math.min(duration,(e.clientX-rect.left)/rect.width*duration));draw(v.currentTime)};
for(let e of data.events){let b=document.createElement('button');b.textContent=fmt(e.start_s)+' · '+e.kind.replaceAll('_',' ');b.onclick=()=>{v.currentTime=e.start_s;draw(e.start_s)};document.getElementById('events').appendChild(b)}draw(0);
</script></body></html>""".replace("MEDIA", media).replace("PAYLOAD", payload)
