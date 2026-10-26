/* Antarmuka canvas offline; solusi fisika berada di model_optik.js. */
(() => {
 'use strict';
 const M=Optik,$=id=>document.getElementById(id),TAU=2*Math.PI;
 const colors=['#67dbd0','#ffb76b','#b9a0ff','#8fbfff','#f58eb9','#cddd84'];
 const state={tab:'b',d:2,lam:1.55,m:0,phase:0,g:4,z:0,playB:false,playC:false};
 let slabData,cp,cmax,comparison=[2,4,6].map(g=>M.coupler(g));
 const plotSpecs=new Map(), mapFrames=new Map();
 const fmt=(x,n=2)=>x.toLocaleString('id-ID',{minimumFractionDigits:n,maximumFractionDigits:n});
 const seq=(a,b,n)=>Array.from({length:n},(_,i)=>a+(b-a)*i/(n-1));
 const series=(label,x,y,color)=>({label,data:x.map((v,i)=>[v,y[i]]),color});
 function surface(id,clear=true){
   const c=$(id),w=Math.round(c.getBoundingClientRect().width),h=Math.round(c.getBoundingClientRect().height),r=window.devicePixelRatio||1;
   if(!w||!h)return null;
   if(c.width!==Math.round(w*r)||c.height!==Math.round(h*r)){c.width=Math.round(w*r);c.height=Math.round(h*r);}
   const ctx=c.getContext('2d');ctx.setTransform(r,0,0,r,0,0);
   if(clear)ctx.clearRect(0,0,w,h);
   ctx.font='12px system-ui';return {c,ctx,w,h,r};
 }
 function frame(id,xlim,ylim,xlabel,ylabel,title,grid=true){
   const s=surface(id);if(!s)return null;const {ctx,w,h}=s;
   ctx.fillStyle='#121e2d';ctx.fillRect(0,0,w,h);
   const left=w<450?65:76,right=18,top=31,bottom=51;
   const pw=w-left-right,ph=h-top-bottom;
   const X=v=>left+(v-xlim[0])/(xlim[1]-xlim[0])*pw,Y=v=>top+ph-(v-ylim[0])/(ylim[1]-ylim[0])*ph;
   ctx.fillStyle='#e8eef5';ctx.textAlign='left';ctx.fillText(title,left,16);
   ctx.lineWidth=1;const ticks=w<450?3:5;
   for(let i=0;i<=ticks;i++){
     const v=xlim[0]+(xlim[1]-xlim[0])*i/ticks,x=X(v);
     if(grid){ctx.strokeStyle='#283748';ctx.beginPath();ctx.moveTo(x,top);ctx.lineTo(x,top+ph);ctx.stroke();}
     ctx.fillStyle='#a9b9c9';ctx.textAlign=i===0?'left':i===ticks?'right':'center';ctx.fillText(fmt(v,Math.abs(v)<20?1:0),x,top+ph+20);
   }
   for(let i=0;i<=4;i++){
     const v=ylim[0]+(ylim[1]-ylim[0])*i/4,y=Y(v);
     if(grid){ctx.strokeStyle='#283748';ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(left+pw,y);ctx.stroke();}
     ctx.fillStyle='#a9b9c9';ctx.textAlign='right';ctx.fillText(fmt(v,ylim[1]-ylim[0]<.1?4:Math.abs(v)<20?1:0),left-9,y+4);
   }
   ctx.strokeStyle='#536276';ctx.strokeRect(left,top,pw,ph);
   ctx.textAlign='center';ctx.fillStyle='#c9d4e0';ctx.fillText(xlabel,left+pw/2,h-8);
   ctx.save();ctx.translate(15,top+ph/2);ctx.rotate(-Math.PI/2);ctx.fillText(ylabel,0,0);ctx.restore();
   return {...s,left,top,pw,ph,X,Y,xlim,ylim};
 }
 function drawPlot(id,spec){
   plotSpecs.set(id,spec);
   const f=frame(id,spec.xlim,spec.ylim,spec.xlabel,spec.ylabel,spec.title||'');if(!f)return;
   spec.frame=f;const {ctx,left,top,pw,ph,X,Y}=f;
   ctx.save();ctx.beginPath();ctx.rect(left,top,pw,ph);ctx.clip();
   for(const band of spec.bands||[]){ctx.fillStyle='rgba(143,191,255,.10)';ctx.fillRect(X(band[0]),top,X(band[1])-X(band[0]),ph);}
   for(const line of spec.lines){ctx.strokeStyle=line.color;ctx.lineWidth=2;ctx.beginPath();let active=false;
     for(const [x,y] of line.data){if(y===null||!Number.isFinite(y)){active=false;continue;}if(!active){ctx.moveTo(X(x),Y(y));active=true;}else ctx.lineTo(X(x),Y(y));}ctx.stroke();}
   for(const x of spec.vlines||[]){ctx.strokeStyle='#d4dde8';ctx.lineWidth=1;ctx.setLineDash([4,4]);ctx.beginPath();ctx.moveTo(X(x),top);ctx.lineTo(X(x),top+ph);ctx.stroke();ctx.setLineDash([]);}
   for(const p of spec.points||[]){ctx.beginPath();ctx.fillStyle=p.color;ctx.arc(X(p.x),Y(p.y),4,0,TAU);ctx.fill();ctx.strokeStyle='#121e2d';ctx.stroke();}
   ctx.restore();
 }
 function interpolate(data,x){
   let lo=0,hi=data.length-1;while(hi-lo>1){let mid=(lo+hi)>>1;if(data[mid][0]<=x)lo=mid;else hi=mid;}
   const a=data[lo],b=data[hi];if(a[1]===null||b[1]===null)return null;
   return a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0]);
 }
 function hover(id,event){
   const p=plotSpecs.get(id);if(!p||!p.frame)return;const f=p.frame,box=$(id).getBoundingClientRect(),px=event.clientX-box.left;
   if(px<f.left||px>f.left+f.pw)return;
   const x=f.xlim[0]+(px-f.left)/f.pw*(f.xlim[1]-f.xlim[0]);
   drawPlot(id,p);const {ctx}=p.frame;ctx.strokeStyle='#b5c5d5';ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(px,f.top);ctx.lineTo(px,f.top+f.ph);ctx.stroke();ctx.setLineDash([]);
   const values=p.lines.map(l=>{const y=interpolate(l.data,x);if(y===null)return l.label+': tidak terikat';ctx.fillStyle=l.color;ctx.beginPath();ctx.arc(px,f.Y(y),3.5,0,TAU);ctx.fill();return l.label+': '+fmt(y,p.ylabel.startsWith('n')?6:3);});
   $('hint-'+id).textContent=(p.xname||'x')+' = '+fmt(x,2)+' µm · '+values.join(' · ');
 }
 function legend(id,lines){$(id).innerHTML=lines.map(l=>'<span style="--series:'+l.color+'">'+l.label+'</span>').join('');}
 function palette(v,signed){
   let stops=signed?[[40,76,187],[16,25,38],[255,186,102]]:[[16,25,38],[18,101,134],[88,211,189],[244,231,163]];
   let t=Math.max(0,Math.min(1,signed?(v+1)/2:v))*(stops.length-1),i=Math.min(stops.length-2,Math.floor(t)),u=t-i;
   return stops[i].map((v,j)=>Math.round(v+(stops[i+1][j]-v)*u));
 }
 const palettes=[false,true].map(s=>Array.from({length:1025},(_,i)=>palette(s?i/512-1:i/1024,s)));
 function heat(id,xlim,ylim,title,bounds,signed,value){
   const f=frame(id,xlim,ylim,'Propagasi z (µm)','Posisi x (µm)',title,false);if(!f)return;
   const nx=Math.min(900,Math.round(f.pw)),ny=230,off=document.createElement('canvas');off.width=nx;off.height=ny;
   const ctx=off.getContext('2d'),im=ctx.createImageData(nx,ny),pal=palettes[signed?1:0];
   for(let y=0;y<ny;y++){const x=ylim[1]-(ylim[1]-ylim[0])*y/(ny-1);
     for(let j=0;j<nx;j++){const z=xlim[0]+(xlim[1]-xlim[0])*j/(nx-1),v=value(x,z),index=Math.max(0,Math.min(1024,Math.round((signed?(v+1)/2:v)*1024))),rgb=pal[index],i=4*(y*nx+j);im.data[i]=rgb[0];im.data[i+1]=rgb[1];im.data[i+2]=rgb[2];im.data[i+3]=255;}}
   ctx.putImageData(im,0,0);f.ctx.drawImage(off,f.left,f.top,f.pw,f.ph);
   f.ctx.strokeStyle='rgba(226,235,245,.55)';f.ctx.lineWidth=1;
   for(const b of bounds){f.ctx.beginPath();f.ctx.moveTo(f.left,f.Y(b));f.ctx.lineTo(f.left+f.pw,f.Y(b));f.ctx.stroke();}
   mapFrames.set(id,f);return f;
 }
 function drawSlabMap(){
   const m=slabData.mode,extent=slabData.extent;
   // Cache transverse samples on each scan line during the raster loop.
   let oldX=null,e=0;
   heat('map-b',[0,8],[-extent,extent],'TE'+m.m+' · d '+fmt(state.d)+' µm · λ₀ '+fmt(state.lam)+' µm',[-state.d/2,state.d/2],true,(x,z)=>{if(x!==oldX){e=M.field(x,m);oldX=x;}return e*Math.cos(m.beta*z-state.phase);});
   $('phase-val').textContent=fmt(state.phase)+' rad';$('phase').value=state.phase;
 }
 function computeSlab(){
   const modes=M.slab(state.d,state.lam);state.m=Math.min(state.m,modes.length-1);
   $('mode').innerHTML=modes.map(m=>'<option value="'+m.m+'">TE'+m.m+'</option>').join('');$('mode').value=state.m;
   const mode=modes[state.m],extent=Math.max(state.d/2+3,Math.min(40,state.d/2+4/mode.q));
   const xs=seq(-extent,extent,601),e=xs.map(x=>M.field(x,mode));
   function sweep(x,fn){const vals=x.map(fn),n=Math.max(...vals.map(m=>m.length));return Array.from({length:n},(_,i)=>series('TE'+i,x,vals.map(a=>a[i]?.neff??null),colors[i%colors.length]));}
   const ds=seq(.5,12,231),ls=seq(.8,2.2,141);
   slabData={mode,modes,extent,xs,e,ds,ls,dl:sweep(ds,d=>M.slab(d,state.lam)),ll:sweep(ls,l=>M.slab(state.d,l))};
   window.OptikKeterangan?.updateB(slabData,state);
   $('d-val').textContent=fmt(state.d)+' µm';$('lambda-val').textContent=fmt(state.lam)+' µm';
   $('slab-metrics').innerHTML='<span>n efektif <b>'+fmt(mode.neff,6)+'</b></span><span>β <b>'+fmt(mode.beta,5)+' µm⁻¹</b></span><span>Mode terikat <b>'+modes.length+'</b></span><span>Panjang gelombang dalam pandu <b>'+fmt(state.lam/mode.neff,3)+' µm</b></span>';
 }
 function drawSlab(){
   if(state.tab!=='b')return;const s=slabData;
   drawSlabMap();
   drawPlot('field-b',{xlim:[-s.extent,s.extent],ylim:[-1.1,1.1],xlabel:'Posisi melintang x (µm)',ylabel:'Medan / intensitas relatif',title:'TE'+state.m+' · arsiran = teras',bands:[[-state.d/2,state.d/2]],lines:[series('ψₘ',s.xs,s.e,colors[0]),series('|ψₘ|²',s.xs,s.e.map(e=>e*e),colors[1])]});
   const base={ylim:[M.NS,M.NC],ylabel:'n efektif (tanpa satuan)',points:[]};
   drawPlot('disp-d',{...base,xlim:[.5,12],xlabel:'Ketebalan penuh d (µm)',xname:'d',title:'λ₀ = '+fmt(state.lam)+' µm',lines:s.dl,vlines:[state.d],points:[{x:state.d,y:s.mode.neff,color:colors[state.m%6]}]});
   drawPlot('disp-lambda',{...base,xlim:[.8,2.2],xlabel:'Panjang gelombang vakum λ₀ (µm)',xname:'λ₀',title:'d = '+fmt(state.d)+' µm · dispersi pandu',lines:s.ll,vlines:[state.lam],points:[{x:state.lam,y:s.mode.neff,color:colors[state.m%6]}]});
   legend('legend-d',s.dl);legend('legend-lambda',s.ll);
 }
 function computeCoupler(){
   cp=M.coupler(state.g);
   cmax=Math.max(...seq(-12,12,2401).map(x=>{const [e,o]=M.basis(x,cp);return .5*(Math.abs(e)+Math.abs(o))**2;}));
   $('gap-val').textContent=fmt(state.g)+' µm';
   $('coupler-metrics').innerHTML='<span>κ <b>'+fmt(cp.kappa,7)+' µm⁻¹</b></span><span>Jarak 50:50 <b>'+fmt(cp.Lc/2)+' µm</b></span><span>Transfer penuh pertama <b>'+fmt(cp.Lc)+' µm</b></span>';
 }
 function drawCouplerMap(){
   let oldX=null,e=0,o=0;
   heat('map-c',[0,1400],[-12,12],'g = '+fmt(state.g)+' µm · pandu b di atas, a di bawah',[-state.g/2-2,-state.g/2,state.g/2,state.g/2+2],false,(x,z)=>{if(x!==oldX){[e,o]=M.basis(x,cp);oldX=x;}return .5*(e*e+o*o+2*e*o*Math.cos(2*cp.kappa*z))/cmax;});
 }
 function drawCoupler(){
   if(state.tab!=='c')return;
   drawCouplerMap();drawPosition();
 }
 function drawPosition(){
   if(state.tab!=='c')return;
   const f=mapFrames.get('map-c'),over=surface('cursor-c');
   if(f&&over){over.ctx.strokeStyle='#fff';over.ctx.lineWidth=2;over.ctx.setLineDash([5,5]);over.ctx.beginPath();over.ctx.moveTo(f.X(state.z),f.top);over.ctx.lineTo(f.X(state.z),f.top+f.ph);over.ctx.stroke();over.ctx.setLineDash([]);}
   $('position').value=state.z;$('z-val').textContent=fmt(state.z,1)+' µm';
   window.OptikKeterangan?.updateC(cp,state);
   const [pa,pb]=M.power(state.z,cp);$('bar-a').style.width=100*pa+'%';$('bar-b').style.width=100*pb+'%';$('power-a').textContent=fmt(100*pa,1)+'%';$('power-b').textContent=fmt(100*pb,1)+'%';
   const x=seq(-12,12,601),z=seq(0,1400,701);
   drawPlot('slice-c',{xlim:[-12,12],ylim:[0,1.05],xlabel:'Posisi melintang x (µm)',ylabel:'Intensitas relatif',title:'z = '+fmt(state.z,1)+' µm · skala warna tetap',bands:[[-state.g/2-2,-state.g/2],[state.g/2,state.g/2+2]],lines:[series('|Eᵧ|²',x,x.map(v=>M.intensity(v,state.z,cp)/cmax),colors[0])]});
   drawPlot('power-c',{xlim:[0,1400],ylim:[0,1.05],xlabel:'Jarak propagasi z (µm)',xname:'z',ylabel:'Daya / P₀',title:'g = '+fmt(state.g)+' µm',lines:[series('a',z,z.map(v=>M.power(v,cp)[0]),colors[0]),series('b',z,z.map(v=>M.power(v,cp)[1]),colors[1])],vlines:[state.z],points:[{x:state.z,y:pa,color:colors[0]},{x:state.z,y:pb,color:colors[1]}]});
   drawPlot('compare-c',{xlim:[0,1400],ylim:[0,1.05],xlabel:'Jarak propagasi z (µm)',xname:'z',ylabel:'Pᵦ / P₀',title:'Tiga celah · sumbu z sama',lines:comparison.map((c,i)=>series('g='+c.g,z,z.map(v=>M.power(v,c)[1]),colors[i])),vlines:[state.z]});
   $('gap-table').innerHTML=comparison.map(c=>'<tr><td>'+fmt(c.g,0)+'</td><td>'+fmt(c.kappa,7)+'</td><td>'+fmt(c.Lc/2)+'</td><td>'+fmt(c.Lc)+'</td><td>'+fmt(M.power(state.z,c)[1],4)+'</td></tr>').join('');
 }
 function setPlay(which,on){state[which==='b'?'playB':'playC']=on;$('play-'+which).textContent=on?'Ⅱ Jeda':which==='b'?'▶ Jalankan fase':'▶ Ikuti propagasi';}
 function switchTab(t){state.tab=t;setPlay('b',false);setPlay('c',false);for(const a of ['b','c']){$('part-'+a).hidden=a!==t;$('tab-'+a).setAttribute('aria-selected',String(a===t));}if(t==='b')drawSlab();else drawCoupler();}
 function download(name,data,type){const a=document.createElement('a'),u=URL.createObjectURL(new Blob([data],{type}));a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
 function csv(rows){return '\uFEFF'+rows.map(r=>r.map(v=>v===null?'':v).join(',')).join('\r\n');}
 $('tab-b').onclick=()=>switchTab('b');$('tab-c').onclick=()=>switchTab('c');
 ['b','c'].forEach(t=>$('tab-'+t).onkeydown=e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();const to=t==='b'?'c':'b';switchTab(to);$('tab-'+to).focus();}});
 for(const [id,key] of [['thickness','d'],['wavelength','lam'],['mode','m']])$(id).addEventListener('input',()=>{state[key]=Number($(id).value);computeSlab();drawSlab();});
 $('phase').oninput=()=>{setPlay('b',false);state.phase=Number($('phase').value);drawSlabMap();};
 $('gap').oninput=()=>{state.g=Number($('gap').value);computeCoupler();drawCoupler();};
 $('position').oninput=()=>{setPlay('c',false);state.z=Number($('position').value);drawPosition();};
 $('play-b').onclick=()=>setPlay('b',!state.playB);
 $('play-c').onclick=()=>{if(state.z>=1400)state.z=0;setPlay('c',!state.playC);};
 $('half-c').onclick=()=>{setPlay('c',false);state.z=cp.Lc/2;drawPosition();};
 $('full-c').onclick=()=>{setPlay('c',false);state.z=cp.Lc;drawPosition();};
 for(const id of ['field-b','disp-d','disp-lambda','slice-c','power-c','compare-c']){$(id).addEventListener('pointermove',e=>hover(id,e));$(id).addEventListener('pointerleave',()=>{const p=plotSpecs.get(id);if(p)drawPlot(id,p);});}
 document.querySelectorAll('[data-save]').forEach(btn=>btn.onclick=()=>{
   const id=btn.dataset.save,p=plotSpecs.get(id);if(p)drawPlot(id,p);
   const source=$(id),canvas=document.createElement('canvas'),r=window.devicePixelRatio||1;
   const legendItems=p?p.lines.map(l=>({text:l.label,color:l.color})):[{text:id==='map-b'?'Biru: negatif · gelap: nol · jingga: positif':'Gelap: 0 · kuning: 1 · intensitas relatif',color:'#e8eef5'}];
   canvas.width=source.width;canvas.height=source.height+Math.ceil(58*r);const ctx=canvas.getContext('2d');ctx.fillStyle='#121e2d';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(source,0,0);if(id==='map-c')ctx.drawImage($('cursor-c'),0,0);
   ctx.font=(12*r)+'px system-ui';let lx=20*r,ly=source.height+20*r;
   for(const item of legendItems){const length=ctx.measureText(item.text).width+45*r;if(lx+length>canvas.width-10*r){lx=20*r;ly+=20*r;}ctx.fillStyle=item.color;ctx.fillRect(lx,ly-5*r,18*r,3*r);ctx.fillStyle='#e8eef5';ctx.fillText(item.text,lx+25*r,ly);lx+=length;}
   const name=id+'_'+(state.tab==='b'?'d'+state.d+'_lambda'+state.lam+'_TE'+state.m:'gap'+state.g+'_z'+state.z.toFixed(1))+'.png';
   canvas.toBlob(blob=>{if(blob)download(name,blob,'image/png');},'image/png');
 });
 $('csv-b').onclick=()=>{
   const rows=[['jenis','d_um','lambda_um','mode','x_um','Ey_relatif','intensitas_relatif','neff']];
   slabData.xs.forEach((x,i)=>rows.push(['profil',state.d,state.lam,state.m,x,slabData.e[i],slabData.e[i]**2,slabData.mode.neff]));
   for(const d of slabData.ds)for(const m of M.slab(d,state.lam))rows.push(['sweep_d',d,state.lam,m.m,'','','',m.neff]);
   for(const l of slabData.ls)for(const m of M.slab(state.d,l))rows.push(['sweep_lambda',state.d,l,m.m,'','','',m.neff]);
   download('bagian_B_d'+state.d+'_lambda'+state.lam+'.csv',csv(rows),'text/csv;charset=utf-8');
 };
 $('csv-c').onclick=()=>{
   const rows=[['g_um','d_um','lambda_um','z_um','Pa_P0','Pb_P0','kappa_per_um','Lc_um']];
   const gaps=[...new Set([2,4,6,state.g])];for(const g of gaps){const c=M.coupler(g);for(const z of seq(0,1400,701))rows.push([g,2,1.55,z,...M.power(z,c),c.kappa,c.Lc]);}
   download('bagian_C_gap'+state.g+'.csv',csv(rows),'text/csv;charset=utf-8');
 };
 let last=0,elapsed=0;function tick(time){const dt=last?Math.min(.1,(time-last)/1000):0;last=time;elapsed+=dt;
   if(elapsed>.05){const step=elapsed;elapsed=0;if(state.playB&&state.tab==='b'){state.phase=(state.phase+step*1.5)%TAU;drawSlabMap();}if(state.playC&&state.tab==='c'){state.z=Math.min(1400,state.z+step*100);drawPosition();if(state.z===1400)setPlay('c',false);}}
   requestAnimationFrame(tick);
 }
 let resize;window.addEventListener('resize',()=>{clearTimeout(resize);resize=setTimeout(()=>state.tab==='b'?drawSlab():drawCoupler(),120);});
 document.addEventListener('visibilitychange',()=>{if(document.hidden){setPlay('b',false);setPlay('c',false);}});
 computeSlab();computeCoupler();drawSlab();requestAnimationFrame(tick);
})();
