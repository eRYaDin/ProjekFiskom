// Jalankan dengan Node.js: node kode/uji_model_optik.cjs
// Menguji angka acuan Python, batas fisika, dan normalisasi medan.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const M=require('./model_optik.js');
const ref=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/hasil.json'),'utf8'));
const near=(a,b,tol,label)=>assert.ok(Math.abs(a-b)<tol,`${label}: ${a} vs ${b}`);
near(M.slab()[0].neff,ref.single.neff,1e-11,'Slab vs Python');
for(const r of ref.couplers){const c=M.coupler(r.g);near(c.Lc,r.Lc,1e-6,'Lc vs Python');near(M.power(c.Lc,c)[1],1,1e-12,'Transfer penuh');near(M.power(c.Lc/2,c)[1],.5,1e-12,'50:50');
  for(const z of [0,123,c.Lc/2,c.Lc,1400])near(M.power(z,c).reduce((a,b)=>a+b),1,1e-14,'Konservasi daya modal');
  // Field continuity at both sides of each interface, and derivative continuity.
  const dx=1e-5;
  for(let i=0;i<2;i++)for(const x of [c.g/2,c.g/2+2]){
    const f=x=>M.superFieldRaw(x,c.ne[i],c.g,!!i);
    near(f(x-dx),f(x+dx),2e-4,'Kontinuitas E');
    near((f(x)-f(x-dx))/dx,(f(x+dx)-f(x))/dx,1e-4,'Kontinuitas turunan');
  }
  // Simpson integral over a sufficiently large interval, power-normalized modes.
  const n=24000,xmax=70,dxi=2*xmax/n;let norms=[0,0],cross=0,pz=[0,0,0];
  for(let i=0;i<=n;i++){
    const x=-xmax+i*dxi,w=(i===0||i===n?1:i%2?4:2)*dxi/3,[e,o]=M.basis(x,c);
    norms[0]+=w*c.be*e*e;norms[1]+=w*c.bo*o*o;cross+=w*e*o;
    [0,c.Lc/2,c.Lc].forEach((z,j)=>{pz[j]+=w*.5*(c.be*e*e+c.bo*o*o+(c.be+c.bo)*e*o*Math.cos(2*c.kappa*z));});
    near(M.intensity(x,0,c),M.intensity(-x,c.Lc,c),1e-12,'Pertukaran profil a ke b');
    assert.ok(M.intensity(x,c.Lc/2,c)>=-1e-14,'Intensitas nonnegatif');
  }
  norms.forEach(a=>near(a,1,2e-7,'Normalisasi supermode'));near(cross,0,1e-10,'Ortogonalitas');pz.forEach(a=>near(a,1,2e-7,'Integral fluks sepanjang z'));
}
for(const d of [.5,2,4,8,12])for(const l of [.8,1.55,2.2]){
  const modes=M.slab(d,l);assert.equal(modes.length,Math.ceil(2*d*Math.sqrt(M.NC**2-M.NS**2)/l));
  for(const m of modes){assert.ok(m.neff>M.NS&&m.neff<M.NC);const eps=1e-6;near(M.field(d/2-eps,m),M.field(d/2+eps,m),1e-5,'Kontinuitas slab');}
}
assert.ok(M.slab(2,.8)[0].neff>M.slab(2,2.2)[0].neff,'Dispersi pandu');
const cutoff=1.55/(2*Math.sqrt(M.NC**2-M.NS**2));
assert.equal(M.slab(cutoff,1.55).length,1);assert.equal(M.slab(cutoff+.001,1.55).length,2);
assert.ok(M.coupler(2).Lc<M.coupler(4).Lc&&M.coupler(4).Lc<M.coupler(6).Lc);
console.log('LULUS: acuan Python, batas mode/cutoff, dispersi, kontinuitas E dan E\', normalisasi supermode, ortogonalitas, konservasi fluks, dan pertukaran profil.');
