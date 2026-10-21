const vm = require('node:vm');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const {pending, finished, wrapper} = JSON.parse(fs.readFileSync(0, 'utf8'));
const script = html => html.match(/<script>([\s\S]*?)<\/script>/)[1];
function scene(html, decision) {
  const nodes = {}, messages = [];
  function element() { return {style:{},dataset:{},disabled:false,textContent:'', handlers:{},
    classList:{add(){},remove(){}},appendChild(){},setPointerCapture(){},
    getBoundingClientRect(){return {left:100,top:100,right:300,bottom:300,width:200,height:200}},
    addEventListener(type,fn){this.handlers[type]=fn}}; }
  const document = {body:{dataset:{decision}},getElementById(id){return nodes[id] ||= element()},
    createElement:element,createTextNode:text=>({text})};
  vm.runInNewContext(script(html), {document,window:{parent:{postMessage:m=>messages.push(m)}}, setTimeout:f=>f()});
  return {nodes,messages};
}
let a = scene(pending, 'pending');
assert.equal(a.messages.length, 0, 'scene must not start analysis by rendering');
a.nodes.throw.handlers.click(); a.nodes.throw.handlers.click();
assert.deepEqual(JSON.parse(JSON.stringify(a.messages)), [{type:'cart:toss',token:'test-token'}]);
assert.equal(a.nodes.throw.disabled, true);
let b = scene(pending,'pending');
b.nodes.product.handlers.pointerdown({clientX:100,clientY:100,pointerId:1});
b.nodes.product.handlers.pointermove({clientX:180,clientY:110});
b.nodes.product.handlers.pointerup();
assert.equal(b.messages.length,1,'drag into cart triggers analysis');
let c=scene(pending,'pending');
c.nodes.product.handlers.keydown({key:'Enter',preventDefault(){}});
assert.equal(c.messages.length,1,'keyboard triggers analysis');
let d=scene(finished,'wait');
assert.equal(d.messages.length,0,'result replay must never trigger another model call');
const sent=[], parent={postMessage:m=>sent.push(m)}, inner={contentWindow:{},srcdoc:''};
let receive;
vm.runInNewContext(script(wrapper), {document:{getElementById:()=>inner},window:{parent,
  addEventListener:(type,fn)=>receive=fn}});
assert.equal(sent[0].type,'streamlit:componentReady');
receive({source:parent,data:{type:'streamlit:render',args:{html:'hello',token:'test-token'}}});
assert.equal(inner.srcdoc,'hello');
receive({source:{},data:{type:'cart:toss',token:'test-token'}});
receive({source:inner.contentWindow,data:{type:'cart:toss',token:'stale-token'}});
assert.equal(sent.filter(m=>m.type==='streamlit:setComponentValue').length,0);
receive({source:inner.contentWindow,data:{type:'cart:toss',token:'test-token'}});
assert.equal(sent.filter(m=>m.type==='streamlit:setComponentValue').length,1);
assert.equal(sent.at(-1).value.action,'toss');
console.log('Scene protocol: click, drag, keyboard, replay and token validation passed.');
