"use strict";
/** A local video clock is authoritative; optional signals never fill their gaps. */
const data = JSON.parse(document.getElementById("playerData").textContent);
const rows = data.rows, video = document.getElementById("video"), seek = document.getElementById("seek");
const el = id => document.getElementById(id);
const colors = ["#8198ad", "#98dfca", "#efd28a", "#f5ac75", "#dca0ae"];
const duration = rows.length ? rows[rows.length - 1].video_s : 1;
const validHR = rows.filter(row => row.heart_rate_bpm != null);
const peak = validHR.reduce((best,row) => !best || row.heart_rate_bpm > best.heart_rate_bpm ? row : best, null);
const first = validHR[0];
seek.max = duration;
function time(t) { return `${Math.floor(t/60)}:${String(Math.floor(t%60)).padStart(2,"0")}`; }
function pace(value) { if(value == null) return "—"; const seconds = Math.round(value * 60); return `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,"0")}`; }
function nearest(t) { return rows.reduce((a,b)=>Math.abs(b.video_s-t)<Math.abs(a.video_s-t)?b:a,rows[0]); }
function number(id,value) { el(id).textContent = value == null ? "—" : Math.round(value).toLocaleString(); }
function jump(t) { video.currentTime = Math.max(0,Math.min(duration,t)); draw(video.currentTime); }

el("profile").textContent = data.profile ? `${data.profile.source}. Z2–Z5 start at ${data.profile.lower_bounds_bpm.join(" / ")} bpm.` : "Zones not configured. Enter your watch’s zone thresholds to compare bands.";
el("comparison").textContent = first && peak ? `Start ${Math.round(first.heart_rate_bpm)} bpm${first.heart_rate_zone ? ` · Z${first.heart_rate_zone}` : ""} → peak ${Math.round(peak.heart_rate_bpm)} bpm${peak.heart_rate_zone ? ` · Z${peak.heart_rate_zone}` : ""} at ${time(peak.video_s)}` : "No heart-rate samples in this clip.";

/** Draw actual recorded values; zone colors are descriptive, not danger labels. */
function chart(t) {
  const c=el("chart"),ctx=c.getContext("2d"),left=40,right=466,top=15,bottom=173;
  ctx.clearRect(0,0,c.width,c.height);
  if(!validHR.length){ctx.fillStyle="#b5cacb";ctx.fillText("No heart-rate readings",40,70);return;}
  const low=Math.floor((Math.min(...validHR.map(r=>r.heart_rate_bpm))-8)/10)*10;
  const high=Math.ceil((Math.max(...validHR.map(r=>r.heart_rate_bpm))+8)/10)*10;
  const y=value=>bottom-(value-low)/(high-low)*(bottom-top);
  const x=value=>left+value/duration*(right-left);
  if(data.profile){const limits=[low,...data.profile.lower_bounds_bpm,high]; for(let z=0;z<5;z++){const a=Math.max(low,limits[z]),b=Math.min(high,limits[z+1]);if(b>a){ctx.fillStyle=colors[z]+"26";ctx.fillRect(left,y(b),right-left,y(a)-y(b));ctx.fillStyle=colors[z];ctx.font="11px system-ui";ctx.fillText(`Z${z+1}`,right-24,(y(a)+y(b))/2+4);}}}
  ctx.font="11px system-ui";ctx.fillStyle="#b5cacb";
  for(let v=low;v<=high;v+=10){ctx.fillText(String(v),5,y(v)+4);ctx.strokeStyle="#45616966";ctx.beginPath();ctx.moveTo(left,y(v));ctx.lineTo(right,y(v));ctx.stroke();}
  for(let t=0;t<=duration;t+=15){ctx.fillText(time(t),x(t)-9,198);}
  ctx.strokeStyle="#f5f2e9";ctx.lineWidth=2.5;ctx.beginPath();let pen=false;
  for(const r of rows){if(r.heart_rate_bpm==null){pen=false;continue;}if(pen)ctx.lineTo(x(r.video_s),y(r.heart_rate_bpm));else ctx.moveTo(x(r.video_s),y(r.heart_rate_bpm));pen=true;}ctx.stroke();
  ctx.strokeStyle="#98dfca";ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x(t),top);ctx.lineTo(x(t),bottom);ctx.stroke();
  const r=nearest(t);if(r.heart_rate_bpm!=null){ctx.fillStyle="#fff";ctx.beginPath();ctx.arc(x(t),y(r.heart_rate_bpm),4,0,Math.PI*2);ctx.fill();}
}
function draw(t) {
  if(!rows.length)return;
  const row=nearest(t); el("time").textContent=time(t);number("hr",row.heart_rate_bpm);
  el("zone").textContent=row.heart_rate_zone==null?(data.profile?"No reading":"Not set"):`Zone ${row.heart_rate_zone}`;
  el("zone").style.color=row.heart_rate_zone==null?"#b5cacb":colors[row.heart_rate_zone-1];
  el("pace").textContent=pace(row.pace_min_km);number("cadence",row.cadence_spm);number("elevation",row.altitude_m);number("power",row.running_power_w);seek.value=t;
  const prior=rows.filter(r=>r.spo2_percent!=null&&r.spo2_sample_s<=t).at(-1);
  el("core").textContent=row.core_temperature_c==null?"No reading here":`${row.core_temperature_c.toFixed(2)} °C`;
  el("coreNote").textContent=row.core_temperature_c==null?"Requires an explicit core-sensor export. Never substituted with skin/ambient temperature.":`${row.core_temperature_source} · sample at ${time(row.core_temperature_sample_s)}. No heat-strain conclusion.`;
  const oxygenCurrent = row.spo2_percent != null && Math.abs(t-row.spo2_sample_s) <= 0.5;
  el("oxygen").textContent=oxygenCurrent?`${row.spo2_percent.toFixed(0)}%`:"No reading here";
  el("oxygenNote").textContent=oxygenCurrent?`Spot sample at ${time(row.spo2_sample_s)}. Not a continuous workout signal.`:prior?`Earlier: ${prior.spo2_percent.toFixed(0)}% at ${time(prior.spo2_sample_s)}. Not a current reading.`:"Optional, intermittent signal. No matching sample.";
  chart(t);
}
el("togglePlay").onclick=()=>video.paused?video.play():video.pause();
video.onplay=()=>{el("togglePlay").textContent="Pause replay";};video.onpause=()=>{el("togglePlay").textContent="Play replay";};
video.ontimeupdate=()=>draw(video.currentTime);video.onloadedmetadata=()=>draw(video.currentTime);
seek.oninput=()=>jump(Number(seek.value));el("start").onclick=()=>jump(0);el("peak").disabled=!peak;el("peak").onclick=()=>{if(peak)jump(peak.video_s);};
el("chart").onclick=event=>{const r=event.target.getBoundingClientRect();jump(((event.clientX-r.left)/r.width*480-40)/426*duration);};
for(const event of data.events){const button=document.createElement("button");button.textContent=`${time(event.start_s)} · ${event.kind==="heart_rate_zone_change"?`Zone ${event.from_zone} → ${event.to_zone}`:event.kind.replaceAll("_"," ")}`;button.onclick=()=>jump(event.start_s);el("events").append(button);}
draw(0);
