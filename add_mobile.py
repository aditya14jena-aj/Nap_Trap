#!/usr/bin/env python3
"""
Adds Android / touch support to index.html WITHOUT touching existing game code paths:
  - on-screen joystick + SWING button (left-handed option)
  - Fullscreen and Landscape-lock buttons
  - landscape layout that fills the screen, "rotate your phone" hint
  - screen wake-lock while playing

Usage (in the folder that has index.html):   python add_mobile.py
A backup is written to index.backup.html first. Safe to run once; it refuses to patch twice.
"""
import os
import shutil
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
src = open(PATH, encoding='utf-8').read()

if 'id="tctl"' in src:
    sys.exit('index.html already has the mobile controls - nothing to do.')

shutil.copyfile(PATH, os.path.join(os.path.dirname(PATH), 'index.backup.html'))


def rep(old, new):
    global src
    n = src.count(old)
    if n != 1:
        sys.exit('Could not patch safely (anchor found %d times): %s' % (n, old[:60]))
    src = src.replace(old, new)


# ------------------------------------------------------------------ CSS
CSS = r"""/* ---------- mobile / touch ---------- */
body.touchdev{overscroll-behavior:none; -webkit-tap-highlight-color:transparent}
body.touchdev button{touch-action:manipulation}
.tools{flex-wrap:wrap}
#tctl{
  position:fixed; left:0; right:0; bottom:0; height:62%; z-index:30;
  display:flex; align-items:flex-end; justify-content:space-between; gap:12px;
  pointer-events:none; -webkit-user-select:none; user-select:none; -webkit-touch-callout:none;
  padding:0 max(14px,env(safe-area-inset-right,0px)) max(18px,env(safe-area-inset-bottom,0px)) max(14px,env(safe-area-inset-left,0px));
  --ts:clamp(96px,26vmin,150px);
}
body.lefty #tctl{flex-direction:row-reverse}
#tstick{position:relative; flex:1 1 58%; height:100%; pointer-events:auto; touch-action:none}
#tbase{
  position:absolute; left:8%; bottom:12%; width:var(--ts); height:var(--ts); border-radius:50%;
  border:3px solid rgba(255,255,255,.3); background:rgba(255,255,255,.07); pointer-events:none;
}
#tbase.on{background:rgba(255,255,255,.16); border-color:rgba(255,210,63,.7)}
#tknob{
  position:absolute; left:50%; top:50%; width:44%; height:44%; margin:-22% 0 0 -22%; border-radius:50%;
  background:rgba(255,255,255,.55); border:3px solid rgba(255,255,255,.8); pointer-events:none;
}
#tswing{
  pointer-events:auto; touch-action:none; flex:none; width:var(--ts); height:var(--ts); border-radius:50%;
  border:4px solid #b98f00; background:rgba(255,210,63,.88); color:#16112e;
  font:400 clamp(16px,4.5vmin,24px) var(--display); box-shadow:0 5px 0 #b98f00; cursor:pointer;
  -webkit-user-select:none; user-select:none; margin-bottom:2%;
}
#tswing.on{transform:translateY(4px); box-shadow:0 1px 0 #b98f00; background:#fff3b8}
#trotate{
  position:fixed; left:50%; top:max(8px,env(safe-area-inset-top,0px)); transform:translateX(-50%); z-index:45;
  display:flex; gap:8px; align-items:center; max-width:92vw;
  background:rgba(18,14,38,.94); border:1px solid var(--line); border-radius:999px;
  padding:6px 6px 6px 14px; font:800 12px var(--body); color:var(--ink);
}
#trotate button{font:800 14px var(--body); color:var(--ink); background:rgba(255,255,255,.12); border:0; border-radius:50%; width:26px; height:26px; cursor:pointer}
#ttoast{
  position:fixed; left:50%; bottom:max(76px,env(safe-area-inset-bottom,0px)); transform:translateX(-50%); z-index:50;
  background:rgba(18,14,38,.95); border:1px solid var(--line); border-radius:12px; padding:8px 14px;
  font:800 13px var(--body); max-width:90vw; text-align:center;
}
/* landscape on a touch device: arena fills the screen, header shrinks to a toolbar */
html.land, body.land{overflow:hidden; height:100%; overscroll-behavior:none; -webkit-user-select:none; user-select:none}
body.land{padding:0; background:#000}
body.land .legend{display:none}
body.land .top{position:fixed; left:50%; bottom:max(4px,env(safe-area-inset-bottom,0px)); transform:translateX(-50%); width:auto; margin:0; z-index:40; gap:6px}
body.land .top h1{display:none}
body.land .tools{gap:6px}
body.land .tools button{font-size:11px; padding:5px 9px; background:rgba(18,14,38,.72)}
body.land .stage{
  position:fixed; left:50%; top:50%; transform:translate(-50%,-50%); margin:0;
  width:min(calc(100vw - env(safe-area-inset-left,0px) - env(safe-area-inset-right,0px)), calc(100dvh * 1.6));
  border-radius:0; overflow:hidden; box-shadow:none; background:#0b0818;
}
body.land .ov{position:absolute; inset:0; margin:0; padding:10px; border:0; border-radius:0; background:linear-gradient(180deg,rgba(18,14,38,.35),rgba(18,14,38,.85))}
body.land .card{gap:6px}
body.land .card h2{font-size:20px}
body.land .sub{font-size:12px}
body.land .slots{grid-template-columns:repeat(4,minmax(0,1fr)); gap:6px}
body.land .slot{padding:6px 8px; gap:5px}
body.land .ctl{min-height:0; font-size:10.5px}
body.land .go{font-size:16px; padding:6px 22px}
body.land .ghost{font-size:13px; padding:6px 14px}
body.land .nm{font-size:14px; padding:3px 6px}
body.land .nm.big{font-size:15px}
body.land strong.code{font-size:26px}
body.land .nm, body.land input{-webkit-user-select:text; user-select:text}
</style>
</head>"""
rep("</style>\n</head>", CSS)

# ------------------------------------------------------------------ HTML
HTML = r"""<div id="tctl" hidden>
  <div id="tstick"><div id="tbase"><div id="tknob"></div></div></div>
  <button id="tswing" type="button" aria-label="Swing pillow">SWING</button>
</div>
<div id="trotate" hidden><span>Rotate your phone sideways for a bigger arena</span><button id="trotx" type="button" aria-label="Dismiss">&times;</button></div>
<div id="ttoast" hidden></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>"""
rep('<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>', HTML)

# ------------------------------------------------------------------ input hooks (only two tiny edits)
rep("return {mx:clamp(mx,-1,1),my:clamp(my,-1,1),down:down};",
    "return touchMerge({mx:clamp(mx,-1,1),my:clamp(my,-1,1),down:down});")
rep("  return {mx:mx,my:my,down:down};\n}",
    "  return p.slot===0?touchMerge({mx:mx,my:my,down:down}):{mx:mx,my:my,down:down};\n}")

# ------------------------------------------------------------------ JS
JS = r"""/* ---------- mobile: touch controls, fullscreen, landscape ---------- */
var TOUCH={on:false,mode:0,mx:0,my:0,down:false};
function touchMerge(o){
  if(!TOUCH.on)return o;
  var mx=o.mx+TOUCH.mx,my=o.my+TOUCH.my,l=Math.hypot(mx,my);
  if(l>1){mx/=l;my/=l;}
  return {mx:mx,my:my,down:!!(o.down||TOUCH.down)};
}
(function(){
  var IS_TOUCH=(window.matchMedia&&matchMedia('(pointer:coarse)').matches)||/Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  var root=document.documentElement,body=document.body;
  if(IS_TOUCH)body.classList.add('touchdev');
  function store(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v);}catch(e){}return null;}
  function inGame(){return state==='countdown'||state==='play'||state==='roundEnd'||state==='paused';}

  var ctl=$('tctl'),zone=$('tstick'),base=$('tbase'),knob=$('tknob'),sw=$('tswing'),rot=$('trotate'),toastEl=$('ttoast');
  var tools=document.querySelector('.tools');
  function mk(id){var b=document.createElement('button');b.type='button';b.id=id;tools.insertBefore(b,btnPause);return b;}
  var bTouch=mk('btnTouch'),bLand=mk('btnLand'),bFS=mk('btnFS');

  /* a phone can't drive player 2 from a keyboard: make it a bot by default */
  if(IS_TOUCH&&cfg[1].mode==='human'&&!padFor(1))cfg[1].mode='bot';

  /* ---- toast ---- */
  var tt=0;
  function toast(t){toastEl.textContent=t;toastEl.hidden=false;clearTimeout(tt);tt=setTimeout(function(){toastEl.hidden=true;},2800);}

  /* ---- touch mode: 0 off, 1 right-handed, 2 left-handed ---- */
  var sm=store('naptrap.touch');
  TOUCH.mode=(sm==null||isNaN(+sm))?(IS_TOUCH?1:0):((+sm)%3);
  function applyMode(){
    TOUCH.on=TOUCH.mode>0;
    body.classList.toggle('lefty',TOUCH.mode===2);
    bTouch.textContent='Touch: '+['Off','On','Lefty'][TOUCH.mode];
  }
  bTouch.addEventListener('click',function(){TOUCH.mode=(TOUCH.mode+1)%3;store('naptrap.touch',String(TOUCH.mode));applyMode();bTouch.blur();});
  applyMode();

  /* ---- joystick ---- */
  var sid=null,ox=0,oy=0;
  function stickReset(){
    sid=null;TOUCH.mx=0;TOUCH.my=0;
    base.classList.remove('on');base.style.left='';base.style.top='';base.style.bottom='';
    knob.style.transform='translate(0,0)';
  }
  function stickMove(e){
    var R=base.offsetWidth/2||40,r=zone.getBoundingClientRect();
    var dx=e.clientX-r.left-ox,dy=e.clientY-r.top-oy,d=Math.hypot(dx,dy);
    if(d>R){dx=dx/d*R;dy=dy/d*R;d=R;}
    knob.style.transform='translate('+dx+'px,'+dy+'px)';
    if(d/R<.14){TOUCH.mx=0;TOUCH.my=0;}else{TOUCH.mx=dx/(R*.8);TOUCH.my=dy/(R*.8);}
  }
  zone.addEventListener('pointerdown',function(e){
    if(sid!==null)return;
    e.preventDefault();ensureAudio();
    sid=e.pointerId;try{zone.setPointerCapture(sid);}catch(x){}
    var r=zone.getBoundingClientRect(),R=base.offsetWidth/2||40;
    ox=e.clientX-r.left;oy=e.clientY-r.top;
    base.style.left=(ox-R)+'px';base.style.top=(oy-R)+'px';base.style.bottom='auto';
    base.classList.add('on');stickMove(e);
  });
  zone.addEventListener('pointermove',function(e){if(e.pointerId===sid){e.preventDefault();stickMove(e);}});
  ['pointerup','pointercancel','lostpointercapture'].forEach(function(n){
    zone.addEventListener(n,function(e){if(e.pointerId===sid)stickReset();});
  });

  /* ---- swing button (hold to wind up, release to swing) ---- */
  var swid=null;
  function swRelease(){swid=null;TOUCH.down=false;sw.classList.remove('on');}
  sw.addEventListener('pointerdown',function(e){
    if(swid!==null)return;
    e.preventDefault();ensureAudio();
    swid=e.pointerId;try{sw.setPointerCapture(swid);}catch(x){}
    TOUCH.down=true;sw.classList.add('on');
    if(navigator.vibrate){try{navigator.vibrate(8);}catch(x){}}
  });
  ['pointerup','pointercancel','lostpointercapture'].forEach(function(n){
    sw.addEventListener(n,function(e){if(e.pointerId===swid)swRelease();});
  });
  ctl.addEventListener('contextmenu',function(e){e.preventDefault();});

  /* ---- fullscreen + landscape lock ---- */
  var fsReq=root.requestFullscreen||root.webkitRequestFullscreen;
  var canLock=!!(window.screen&&screen.orientation&&screen.orientation.lock);
  var landLock=false;
  function fsEl(){return document.fullscreenElement||document.webkitFullscreenElement||null;}
  function sync(){
    bFS.textContent=fsEl()?'Exit fullscreen':'Fullscreen';
    bLand.textContent='Landscape: '+(landLock?'On':'Off');
    body.classList.toggle('fs',!!fsEl());
  }
  function lockLand(){
    if(!canLock){toast('Rotate your phone sideways');return Promise.resolve(false);}
    return screen.orientation.lock('landscape').then(function(){landLock=true;sync();return true;})
      .catch(function(){toast('Landscape lock needs fullscreen - or just rotate your phone');return false;});
  }
  function unlockLand(){try{screen.orientation.unlock();}catch(e){}landLock=false;sync();}
  function enterFS(){
    if(!fsReq)return Promise.resolve(false);
    var p;try{p=fsReq.call(root);}catch(e){return Promise.resolve(false);}
    return Promise.resolve(p).then(function(){return true;}).catch(function(){toast('Fullscreen was blocked by the browser');return false;});
  }
  function exitFS(){var f=document.exitFullscreen||document.webkitExitFullscreen;if(f&&fsEl()){try{f.call(document);}catch(e){}}}
  bFS.hidden=!fsReq;
  bLand.hidden=!(IS_TOUCH&&canLock&&fsReq);
  bFS.addEventListener('click',function(){
    if(fsEl()){exitFS();if(landLock)unlockLand();}
    else enterFS().then(function(ok){if(ok&&IS_TOUCH&&canLock)lockLand();});
    bFS.blur();
  });
  bLand.addEventListener('click',function(){
    if(landLock){unlockLand();}
    else if(!fsEl()&&fsReq){enterFS().then(function(ok){if(ok)lockLand();});}
    else lockLand();
    bLand.blur();
  });
  function onFS(){if(!fsEl()&&landLock)unlockLand();sync();layout();}
  document.addEventListener('fullscreenchange',onFS);
  document.addEventListener('webkitfullscreenchange',onFS);

  /* ---- landscape layout ---- */
  function layout(){
    var land=IS_TOUCH&&innerWidth>innerHeight;
    root.classList.toggle('land',land);body.classList.toggle('land',land);
  }
  window.addEventListener('resize',layout);
  window.addEventListener('orientationchange',layout);
  layout();sync();

  /* ---- rotate hint ---- */
  var rotOff=false;
  $('trotx').addEventListener('click',function(){rotOff=true;rot.hidden=true;});

  /* ---- keep the screen awake while playing ---- */
  var wl=null,wlBusy=false;
  function wake(on){
    if(!('wakeLock' in navigator))return;
    if(on&&!wl&&!wlBusy){
      wlBusy=true;
      navigator.wakeLock.request('screen').then(function(l){wlBusy=false;wl=l;l.addEventListener('release',function(){wl=null;});})
        .catch(function(){wlBusy=false;});
    }else if(!on&&wl){try{wl.release();}catch(e){}wl=null;}
  }

  /* ---- show/hide controls with game state ---- */
  setInterval(function(){
    var g=inGame(),show=TOUCH.on&&g;
    if(ctl.hidden===show)ctl.hidden=!show;
    if(!show){
      TOUCH.down=false;TOUCH.mx=0;TOUCH.my=0;
      if(sid!==null)stickReset();
      if(swid!==null)swRelease();
    }
    rot.hidden=!(IS_TOUCH&&g&&innerHeight>innerWidth&&!rotOff);
    wake(IS_TOUCH&&g);
  },150);
})();

/* ---------- main loop ---------- */"""
rep("/* ---------- main loop ---------- */", JS)

open(PATH, 'w', encoding='utf-8').write(src)
print('Done. Backup saved as index.backup.html. Reload the page (hard refresh).')
