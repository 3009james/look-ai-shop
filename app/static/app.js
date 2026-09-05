const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  try { tg.setHeaderColor('#f4efe7'); tg.setBackgroundColor('#f4efe7'); tg.setBottomBarColor?.('#171714'); } catch (_) {}
  try { if (tg.isVersionAtLeast?.('8.0') && tg.requestFullscreen) tg.requestFullscreen(); } catch (_) {}
}

const state = {
  products: [],
  cart: JSON.parse(localStorage.getItem('lookai_cart') || '[]'),
  profile: JSON.parse(localStorage.getItem('lookai_profile') || '{}'),
  category: 'Все',
  query: ''
};
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const money = (n) => `${new Intl.NumberFormat('ru-RU').format(Math.round(n))} ₽`;
const authHeaders = () => ({'Content-Type':'application/json','X-Telegram-Init-Data':tg?.initData || ''});

function toast(text){ const el=$('#toast'); el.textContent=text; el.classList.remove('hidden'); setTimeout(()=>el.classList.add('hidden'),2400); }
function haptic(){ try{tg?.HapticFeedback?.impactOccurred('light')}catch(_){} }

function productCard(p){
  return `<article class="product-card" data-product="${p.id}">
    <div class="image-wrap"><img src="${p.image}" alt="${p.name}" loading="lazy">${p.featured?'<span class="badge">EDITOR’S PICK</span>':''}</div>
    <div class="product-meta"><div><b>${p.name}</b><small>${p.category}</small></div><span class="price">${money(p.price)}</span></div>
  </article>`;
}
function renderProducts(){
  $('#featuredGrid').innerHTML=state.products.filter(p=>p.featured).slice(0,4).map(productCard).join('');
  const cats=['Все',...new Set(state.products.map(p=>p.category))];
  $('#categoryChips').innerHTML=cats.map(c=>`<button class="${c===state.category?'active':''}" data-category="${c}">${c}</button>`).join('');
  const q=state.query.trim().toLowerCase();
  const filtered=state.products.filter(p => (state.category==='Все' || p.category===state.category) && (!q || `${p.name} ${p.category} ${p.description} ${p.tags.join(' ')}`.toLowerCase().includes(q)));
  $('#catalogGrid').innerHTML=filtered.map(productCard).join('') || '<p class="muted">Ничего не найдено.</p>';
  $('#productTotal').textContent=`${filtered.length} товаров`;
  bindProductCards();
}
function bindProductCards(){ $$('[data-product]').forEach(el=>el.onclick=()=>openProduct(Number(el.dataset.product))); }

function route(name){
  $$('.view').forEach(v=>v.classList.remove('active')); $(`#view-${name}`).classList.add('active');
  $$('.bottom-nav button').forEach(b=>b.classList.toggle('active',b.dataset.route===name));
  window.scrollTo({top:0,behavior:'smooth'}); haptic();
}
$$('[data-route]').forEach(b=>b.addEventListener('click',()=>route(b.dataset.route)));

let selectedSize='';
function openProduct(id){
  const p=state.products.find(x=>x.id===id); if(!p)return; selectedSize=p.sizes[0]||'';
  $('#productModalBody').innerHTML=`<div class="product-detail"><img src="${p.image}" alt="${p.name}"><div class="detail-copy"><span class="eyebrow">${p.category}</span><h2>${p.name}</h2><div class="detail-price">${money(p.price)}</div><p>${p.description}</p><p><b>Размер</b></p><div class="size-row">${p.sizes.map((s,i)=>`<button class="${i===0?'active':''}" data-size="${s}">${s}</button>`).join('')}</div><button class="primary full" id="addToCart">Добавить в корзину</button></div></div>`;
  $('#productModal').classList.remove('hidden');
  $$('[data-size]').forEach(b=>b.onclick=()=>{selectedSize=b.dataset.size;$$('[data-size]').forEach(x=>x.classList.remove('active'));b.classList.add('active')});
  $('#addToCart').onclick=()=>{addToCart(p.id,selectedSize);$('#productModal').classList.add('hidden')};
}
$$('[data-close]').forEach(b=>b.onclick=()=>$('#'+b.dataset.close).classList.add('hidden'));
$$('.overlay').forEach(o=>o.addEventListener('click',e=>{if(e.target===o)o.classList.add('hidden')}));

function addToCart(productId,size){
  const existing=state.cart.find(x=>x.product_id===productId&&x.size===size); if(existing)existing.quantity+=1; else state.cart.push({product_id:productId,size,quantity:1});
  persistCart(); toast('Добавлено в корзину'); haptic();
}
function persistCart(){localStorage.setItem('lookai_cart',JSON.stringify(state.cart));renderCart();}
function renderCart(){
  $('#cartCount').textContent=state.cart.reduce((s,x)=>s+x.quantity,0);
  let total=0;
  $('#cartItems').innerHTML=state.cart.map((line,i)=>{const p=state.products.find(x=>x.id===line.product_id); if(!p)return''; total+=p.price*line.quantity; return `<div class="cart-line"><img src="${p.image}" alt=""><div><b>${p.name}</b><small>Размер: ${line.size||'—'} · ${line.quantity} шт.</small><button class="remove" data-remove="${i}">Удалить</button></div><b>${money(p.price*line.quantity)}</b></div>`}).join('') || '<p class="muted">Корзина пока пуста.</p>';
  $('#cartTotal').textContent=money(total); $$('[data-remove]').forEach(b=>b.onclick=()=>{state.cart.splice(Number(b.dataset.remove),1);persistCart()});
}
$('#cartBtn').onclick=()=>{$('#cartDrawer').classList.remove('hidden');renderCart()};

$('#checkoutBtn').onclick=async()=>{
  if(!state.cart.length)return toast('Добавьте товары в корзину');
  try{
    const r=await fetch('/api/orders',{method:'POST',headers:authHeaders(),body:JSON.stringify({customer_name:state.profile.name||'',items:state.cart})});
    if(!r.ok)throw new Error((await r.json()).detail||'Ошибка'); const order=await r.json();
    state.cart=[];persistCart();$('#cartDrawer').classList.add('hidden');
    try{tg?.showAlert?.(`Заказ #${order.id} оформлен на ${money(order.total)}.`)}catch(_){toast(`Заказ #${order.id} оформлен`)}
  }catch(e){toast(`Не удалось оформить: ${e.message}`)}
};

$('#searchToggle').onclick=()=>{$('#searchbar').classList.toggle('hidden'); if(!$('#searchbar').classList.contains('hidden'))$('#searchInput').focus()};
$('#searchInput').addEventListener('input',e=>{state.query=e.target.value;renderProducts();route('catalog')});
$('#categoryChips').addEventListener('click',e=>{if(e.target.dataset.category){state.category=e.target.dataset.category;renderProducts()}});

function loadProfile(){ $('#profileName').value=state.profile.name||'';$('#profileStyle').value=state.profile.style||'';$('#profileSize').value=state.profile.size||'';$('#profileBudget').value=state.profile.budget||''; }
$('#saveProfile').onclick=()=>{state.profile={name:$('#profileName').value.trim(),style:$('#profileStyle').value,size:$('#profileSize').value.trim(),budget:Number($('#profileBudget').value)||null};localStorage.setItem('lookai_profile',JSON.stringify(state.profile));toast('Профиль сохранён')};

async function sendAI(text){
  text=(text||$('#aiInput').value).trim();if(!text)return;
  $('#aiInput').value=''; const box=$('#messages'); box.insertAdjacentHTML('beforeend',`<div class="message user"></div><div class="message assistant loading">Подбираю вещи…</div>`); box.children[box.children.length-2].textContent=text; box.scrollTop=box.scrollHeight;
  const loading=box.lastElementChild;
  try{
    const r=await fetch('/api/ai/stylist',{method:'POST',headers:authHeaders(),body:JSON.stringify({message:text,style:state.profile.style||'',size:state.profile.size||'',budget:state.profile.budget||null})});
    if(!r.ok)throw new Error((await r.json()).detail||'Ошибка AI'); const data=await r.json(); loading.classList.remove('loading');loading.textContent=data.answer;
    const picks=data.product_ids.map(id=>state.products.find(p=>p.id===id)).filter(Boolean);$('#aiResults').innerHTML=picks.map(productCard).join('');$('#aiResultsHead').classList.toggle('hidden',!picks.length);bindProductCards();
  }catch(e){loading.classList.remove('loading');loading.textContent='Не удалось получить подбор. Проверьте настройки сервера и попробуйте ещё раз.'}
  box.scrollTop=box.scrollHeight;
}
$('#aiSend').onclick=()=>sendAI();$('#aiInput').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendAI()}});$$('.quick-prompts button').forEach(b=>b.onclick=()=>sendAI(b.textContent));

async function init(){
  try{const r=await fetch('/api/products');state.products=await r.json();renderProducts();renderCart();loadProfile();}catch(e){toast('Не удалось загрузить каталог')}
}
init();
