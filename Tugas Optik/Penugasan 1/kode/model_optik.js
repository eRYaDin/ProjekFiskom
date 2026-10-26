/* Model numerik TE slab simetris. Semua panjang: µm. Tanpa dependensi. */
(function(root) {
  'use strict';
  const NC=1.51, NS=1.50, PI=Math.PI;
  function bisect(f,a,b) {
    let fa=f(a);
    if(fa*f(b)>0) throw Error('Akar tidak terkurung');
    for(let i=0;i<90;i++) {const c=(a+b)/2, fc=f(c); if(b-a<1e-13)return c;
      if(fa*fc<=0)b=c;else{a=c;fa=fc;}}
    return (a+b)/2;
  }
  function slab(d=2,lam=1.55) {
    if(!(d>0&&lam>0))throw Error('d dan lambda harus positif');
    const k=2*PI/lam,V=k*d*Math.sqrt(NC*NC-NS*NS), out=[];
    for(let m=0;m<=Math.floor(V/PI);m++) {
      if(V<=m*PI+1e-12)continue;
      const f=b=>V*Math.sqrt(1-b)-m*PI-2*Math.atan(Math.sqrt(b/(1-b)));
      const b=bisect(f,1e-15,1-1e-15),neff=Math.sqrt(NS*NS+b*(NC*NC-NS*NS));
      out.push({m,b,neff,beta:k*neff,h:k*Math.sqrt(NC*NC-neff*neff),q:k*Math.sqrt(neff*neff-NS*NS),V,d,lam});
    }return out;
  }
  function field(x,m) {
    const a=m.d/2;
    if(Math.abs(x)<=a)return m.m%2?Math.sin(m.h*x):Math.cos(m.h*x);
    return (m.m%2?Math.sign(x)*Math.sin(m.h*a):Math.cos(m.h*a))*Math.exp(-m.q*(Math.abs(x)-a));
  }
  function residual(ne,g,odd) {
    const k=2*PI/1.55,q=k*Math.sqrt(ne*ne-NS*NS),h=k*Math.sqrt(NC*NC-ne*ne),t=q*g/2;
    const e=odd?Math.sinh(t)/q:Math.cosh(t), v=odd?Math.cosh(t):q*Math.sinh(t);
    return -e*h*Math.sin(h*2)+v*Math.cos(h*2)+q*(e*Math.cos(h*2)+v*Math.sin(h*2)/h);
  }
  function superFieldRaw(x,ne,g,odd) {
    const k=2*PI/1.55,q=k*Math.sqrt(ne*ne-NS*NS),h=k*Math.sqrt(NC*NC-ne*ne), a=g/2,r=Math.abs(x);
    const e0=odd?Math.sinh(q*a)/q:Math.cosh(q*a),v0=odd?Math.cosh(q*a):q*Math.sinh(q*a);
    let e;
    if(r<a)e=odd?Math.sinh(q*r)/q:Math.cosh(q*r);
    else if(r<=a+2){let t=r-a;e=e0*Math.cos(h*t)+v0*Math.sin(h*t)/h;}
    else e=(e0*Math.cos(h*2)+v0*Math.sin(h*2)/h)*Math.exp(-q*(r-a-2));
    // Odd mode positive on the negative-x input guide (a).
    return odd?-Math.sign(x)*e:e;
  }
  function norm(ne,g,odd) {
    // Simpson integral through all finite layers, plus exact exponential tails.
    const a=g/2+2,N=1200,dx=a/N;
    let sum=0;
    for(let i=0;i<=N;i++){const e=superFieldRaw(i*dx,ne,g,odd);sum+=(i===0||i===N?1:i%2?4:2)*e*e;}
    const q=2*PI/1.55*Math.sqrt(ne*ne-NS*NS),edge=superFieldRaw(a,ne,g,odd);
    return Math.sqrt(2*sum*dx/3+edge*edge/q);
  }
  const cache=new Map();
  function coupler(g=4) {
    if(g<2||g>6)throw Error('Rentang kopler: 2 sampai 6 µm');
    const key=g.toFixed(6);if(cache.has(key))return cache.get(key);
    const roots=[false,true].map(odd=>{
      const f=ne=>residual(ne,g,odd),hits=[];let a=NS+1e-10,fa=f(a);
      for(let i=1;i<=1600;i++){
        const b=NS+1e-10+(NC-NS-2e-10)*i/1600,fb=f(b);
        if(fa*fb<0)hits.push(bisect(f,a,b));a=b;fa=fb;
      }
      if(hits.length!==1)throw Error('Model memerlukan satu pasangan supermode');
      return hits[0];
    });
    const be=2*PI/1.55*roots[0],bo=2*PI/1.55*roots[1],kappa=(be-bo)/2;
    const cp={g,ne:roots,be,bo,kappa,Lc:PI/(2*kappa),norms:roots.map((n,i)=>norm(n,g,!!i))};
    cache.set(key,cp);return cp;
  }
  function basis(x,c){return c.ne.map((n,i)=>superFieldRaw(x,n,c.g,!!i)/c.norms[i]/Math.sqrt(i?c.bo:c.be));}
  function intensity(x,z,c) {
    const [e,o]=basis(x,c);
    return .5*(e*e+o*o+2*e*o*Math.cos(2*c.kappa*z));
  }
  function power(z,c){const b=Math.sin(c.kappa*z)**2;return [1-b,b];}
  const api={NC,NS,bisect,slab,field,residual,superFieldRaw,coupler,basis,intensity,power};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Optik=api;
})(typeof globalThis!=='undefined'?globalThis:this);
