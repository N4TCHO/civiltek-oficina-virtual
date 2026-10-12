import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js";
const mount=document.getElementById("office3d");if(!mount)throw Error("Falta el contenedor 3D");
const scene=new THREE.Scene();scene.background=new THREE.Color("#a5d7e8");
const camera=new THREE.OrthographicCamera(-13,13,8,-8,.1,120);camera.position.set(24,27,30);camera.lookAt(0,0,0);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:"high-performance"});renderer.setPixelRatio(Math.min(devicePixelRatio,1.7));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;mount.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x759ab5,2.4));const sun=new THREE.DirectionalLight(0xfff5df,2.8);sun.position.set(-12,25,18);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);sun.shadow.camera.left=-24;sun.shadow.camera.right=24;sun.shadow.camera.top=24;sun.shadow.camera.bottom=-24;scene.add(sun);
const mat=(c,roughness=.8)=>new THREE.MeshStandardMaterial({color:c,roughness});const wood=mat("#c38e61"),white=mat("#f3e9d8"),dark=mat("#364a5b"),glass=mat("#58bedb"),screen=mat("#1b384a"),green=mat("#4bb28b"),wall=mat("#fff4e5");
function cube(x,y,z,w,h,d,m,group=scene){const o=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m);o.position.set(x,y,z);o.castShadow=true;o.receiveShadow=true;group.add(o);return o}
function ball(x,y,z,r,m,group=scene){const o=new THREE.Mesh(new THREE.SphereGeometry(r,12,9),m);o.position.set(x,y,z);o.castShadow=true;group.add(o);return o}
cube(0,-.32,0,23,.6,16,mat("#5b8d9c"));cube(0,-.05,0,22.6,.12,15.6,mat("#e5cda9"));cube(0,1.65,-7.78,23,3.5,.18,wall);cube(-11.35,1.65,0,.18,3.5,15.6,wall);
for(let i=-10;i<=10;i+=2.1){cube(i,1.95,-7.64,1.45,1.55,.08,glass);cube(i,1.1,-7.57,1.5,.11,.1,white)}
for(let z=-5.2;z<=5.2;z+=5.1)cube(-11.15,1.65,z,.08,1.5,3.6,glass);
const rooms=[
["Director", -8,-4.7,"#4d94c5"],["Licitaciones",-2.7,-4.7,"#f0b75b"],["Presupuestos",2.7,-4.7,"#a1c87e"],["Calidad MOP",8,-4.7,"#e7a39b"],
["Ingeniería y Obras",-8,0,"#8fbee0"],["Topografía y GIS",-2.7,0,"#d6a6db"],["Prevención de Riesgos",2.7,0,"#efc274"],["Medio Ambiente",8,0,"#89d2a7"],
["Legal y Contratos",-8,4.8,"#d9b69d"],["Documental",-2.7,4.8,"#7fb6cd"],["Finanzas",2.7,4.8,"#b8d38e"],["Auditor",8,4.8,"#a5b5df"]];
const people=[];const clickable=[];const labels=[];
function person(group,x,z,shirtColor,idx){const p=new THREE.Group();p.position.set(x,0,z);group.add(p);const shirt=mat(shirtColor);cube(0,.7,0,.54,.75,.38,shirt,p);cube(-.15,.19,0,.17,.48,.19,dark,p);cube(.15,.19,0,.17,.48,.19,dark,p);ball(0,1.27,0,.28,mat(idx%3===0?"#e5b28e":idx%3===1?"#b77d59":"#f1caa3"),p);const hair=ball(0,1.46,-.05,.27,mat(idx%3===0?"#3c302c":idx%3===1?"#654432":"#322e39"),p);hair.scale.y=.4;const armL=cube(-.37,.79,.17,.18,.5,.2,shirt,p),armR=cube(.37,.79,.17,.18,.5,.2,shirt,p);people.push({root:p,left:armL,right:armR,idx,name:rooms[idx][0]});return p}
function workstation(name,x,z,color,idx){const group=new THREE.Group();group.position.set(x,0,z);scene.add(group);
const floor=cube(0,.035,0,4.9,.11,4.45,mat(color),group);floor.material.color.lerp(new THREE.Color("#ffffff"),.56);
cube(0,.15,-2.13,4.8,.18,.12,white,group);cube(-2.37,.15,0,.12,.18,4.2,white,group);
cube(0,.77,-.65,2.35,.15,1.12,wood,group);for(const dx of [-.92,.92])for(const dz of [-1.02,-.28])cube(dx,.42,dz,.13,.7,.12,dark,group);
cube(0,1.24,-.95,.78,.62,.1,screen,group);cube(0,1.23,-.88,.66,.47,.03,mat("#50d3cf"),group);cube(0,.98,-.95,.08,.17,.08,dark,group);cube(0,.88,-.94,.4,.05,.2,dark,group);
cube(0,.57,.62,.8,.15,.75,mat("#3e7186"),group);cube(0,.9,.9,.8,.75,.13,mat("#3e7186"),group);
person(group,.12,1.5,color,idx);
cube(1.68,.3,1.47,.47,.6,.47,wood,group);cube(1.68,.75,1.47,.62,.32,.62,green,group);ball(1.68,1.06,1.47,.34,green,group);
if(idx%3===0){cube(-1.6,.9,-1.3,.95,.06,.7,white,group);cube(-1.6,1.05,-1.3,.76,.05,.5,mat("#e6c75d"),group)}
const hit=cube(0,.01,0,4.7,.05,4.3,new THREE.MeshBasicMaterial({visible:false}),group);hit.userData.agent=name;clickable.push(hit);
const sign=document.createElement("button");sign.type="button";sign.className="office3d-label";sign.textContent=name;sign.onclick=()=>{window.dispatchEvent(new CustomEvent("civiltek-agent-selected",{detail:{name}}))};mount.appendChild(sign);labels.push({sign,group});
}
rooms.forEach((r,i)=>workstation(...r,i));
const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();let drag=false,downX=0,downY=0,angle=0;const clock=new THREE.Clock();
renderer.domElement.addEventListener("pointerdown",e=>{drag=false;downX=e.clientX;downY=e.clientY});
renderer.domElement.addEventListener("pointermove",e=>{if(e.buttons&&Math.abs(e.clientX-downX)>5){drag=true;angle+=(e.clientX-downX)*.004;downX=e.clientX;camera.position.set(24*Math.cos(angle)+30*Math.sin(angle),27,30*Math.cos(angle)-24*Math.sin(angle));camera.lookAt(0,0,0)}});
renderer.domElement.addEventListener("click",e=>{if(drag)return;const r=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(pointer,camera);const hits=ray.intersectObjects(clickable);if(hits.length)window.dispatchEvent(new CustomEvent("civiltek-agent-selected",{detail:{name:hits[0].object.userData.agent}}))});
let active=false;window.addEventListener("civiltek-job-state",e=>{active=e.detail?.status==="Trabajando"});
function resize(){const w=mount.clientWidth,h=mount.clientHeight;if(!w||!h)return;camera.left=-13;camera.right=13;camera.top=13*h/w;camera.bottom=-13*h/w;camera.updateProjectionMatrix();renderer.setSize(w,h,false)}
new ResizeObserver(resize).observe(mount);resize();
function frame(){requestAnimationFrame(frame);const t=clock.getElapsedTime();for(const p of people){const work=active&&(p.name==="Director"||p.name==="Auditor");const speed=work?7:2;p.left.rotation.x=Math.sin(t*speed+p.idx)*.15;p.right.rotation.x=-Math.sin(t*speed+p.idx)*.15;p.root.position.y=Math.sin(t*speed+p.idx)*.025}for(const l of labels){const v=l.group.position.clone().add(new THREE.Vector3(0,2.15,0)).project(camera);const w=mount.clientWidth,h=mount.clientHeight;l.sign.style.left=((v.x+1)*w/2)+"px";l.sign.style.top=((-v.y+1)*h/2)+"px"}renderer.render(scene,camera)}frame();
