const $ = selector => document.querySelector(selector);
const view = $('#view');
let user, records = [], activeResource, formState, loadVersion = 0;
const admin = () => user?.rol === 'ADMINISTRADOR';
const states = ['PENDIENTE', 'CONFIRMADO', 'ENVIADO', 'ENTREGADO', 'CANCELADO'];
const field = (name, label, type = 'text', extra = {}) => ({name, label, type, ...extra});
const names = [field('nombre', 'Nombre', 'text', {required:true, min:2, max:120})];
const contact = [field('telefono', 'Teléfono', 'tel', {max:30}), field('correo', 'Correo electrónico', 'email', {max:150}), field('direccion', 'Dirección', 'text', {max:250})];
const active = field('activo', 'Estado', 'select', {options:[[1,'Activo'],[0,'Inactivo']], numeric:true, value:1});
const resources = {
  proveedores: {title:'Proveedores', singular:'proveedor', pk:'id_proveedor', subtitle:'Organiza los contactos que abastecen tu negocio.', columns:['id_proveedor','nombre','contacto','telefono','correo','activo'], fields:[...names,field('contacto','Persona de contacto','text',{max:100}),...contact,active]},
  productos: {title:'Productos', singular:'producto', pk:'id_producto', subtitle:'Controla tu catálogo, precios y existencias disponibles.', columns:['id_producto','nombre','precio_compra','precio_venta','existencia','activo'], fields:[field('id_proveedor','Proveedor','select',{source:'proveedores',required:true,numeric:true}),field('nombre','Nombre','text',{required:true,min:2,max:150}),field('descripcion','Descripción','text',{max:500}),field('precio_compra','Precio de compra (COP)','number',{required:true,min:0,max:9999999999.99,step:0.01}),field('margen_porcentaje','Margen sobre costo (%)','number',{required:true,min:0,max:99999.99,step:0.01,value:0}),field('existencia','Existencia disponible','number',{required:true,min:0,max:9999999999,step:1,value:0}),active]},
  clientes: {title:'Clientes', singular:'cliente', pk:'id_cliente', subtitle:'Mantén a mano los datos de tus clientes.', columns:['id_cliente','nombre','telefono','correo','direccion'], fields:[...names,...contact]},
  pedidos: {title:'Pedidos', singular:'pedido', pk:'id_pedido', subtitle:'Consulta tus ventas y acompaña cada pedido hasta su entrega.', columns:['id_pedido','cliente','vendedor','fecha_pedido','estado','total'], fields:[field('id_cliente','Cliente','select',{source:'clientes',required:true,numeric:true}),field('estado','Estado','select',{options:states.map(s=>[s,s]),value:'PENDIENTE'}),field('observaciones','Observaciones','text',{max:500})]},
  pagos: {title:'Pagos', singular:'pago', pk:'id_pago', subtitle:'Registra abonos y consulta el historial de cada pedido.', columns:['id_pago','id_pedido','monto','metodo','fecha_pago','estado'], fields:[field('id_pedido','Pedido','select',{source:'pedidos',required:true,numeric:true}),field('monto','Monto (COP)','number',{required:true,min:0.01,max:9999999999.99,step:0.01}),field('metodo','Método','select',{options:['EFECTIVO','TRANSFERENCIA','TARJETA','OTRO'].map(s=>[s,s])}),field('referencia','Referencia','text',{max:100}),field('estado','Estado','select',{options:[['REGISTRADO','REGISTRADO'],['ANULADO','ANULADO']],value:'REGISTRADO'})]},
  usuarios: {title:'Usuarios', singular:'usuario', pk:'id_usuario', endpoint:'auth/usuarios', subtitle:'Administra las cuentas y los permisos de tu equipo.', columns:['id_usuario','nombre','correo','rol','activo'], fields:[field('nombre','Nombre','text',{required:true,min:2,max:100}),field('correo','Correo electrónico','email',{required:true,max:150}),field('rol','Rol','select',{options:[['VENDEDOR','VENDEDOR'],['ADMINISTRADOR','ADMINISTRADOR']]}),active]},
  detalles: {title:'Detalle', singular:'producto del pedido', pk:'id_detalle', endpoint:'detalle-pedidos', columns:['producto','cantidad','precio_unitario','subtotal'], fields:[field('id_pedido','Pedido','number',{required:true,min:1}),field('id_producto','Producto','select',{source:'productos',required:true,numeric:true}),field('cantidad','Cantidad','number',{required:true,min:1,max:9999999999,step:1,value:1}),field('precio_unitario','Precio aplicado (COP; opcional)','number',{min:0,max:9999999999.99,step:0.01})]}
};
const labels = {id_proveedor:'ID',id_producto:'ID',id_cliente:'ID',id_pedido:'Pedido',id_pago:'ID',id_usuario:'ID',nombre:'Nombre',contacto:'Contacto',telefono:'Teléfono',correo:'Correo',direccion:'Dirección',activo:'Estado',precio_compra:'Costo',precio_venta:'Precio venta',existencia:'Disponible',cliente:'Cliente',vendedor:'Vendedor',fecha_pedido:'Fecha',estado:'Estado',total:'Total',monto:'Monto',metodo:'Método',fecha_pago:'Fecha',rol:'Rol',producto:'Producto',cantidad:'Cantidad',precio_unitario:'Precio unitario',subtotal:'Subtotal',ventas:'Ventas',pedidos:'Pedidos',proveedor:'Proveedor',periodo:'Mes',unidades:'Unidades'};
const currencyFields = new Set(['precio_compra','precio_venta','precio_unitario','monto','total','subtotal','ventas']);
function format(key, value) {
  if (currencyFields.has(key)) return esc(money(value));
  if (key === 'activo') return `<span class="badge-soft ${Number(value) ? '' : 'muted'}">${Number(value) ? 'Activo' : 'Inactivo'}</span>`;
  if (key === 'estado') return `<span class="badge-soft ${['CANCELADO','ANULADO'].includes(value) ? 'muted' : ''}">${esc(value)}</span>`;
  if (key.startsWith('fecha_')) return esc(value ? new Date(value).toLocaleDateString('es-CO') : '—');
  return esc(value ?? '—');
}
function notify(message, error = false) {
  const box = $('#message'); box.textContent = message; box.hidden = false;
  box.className = `alert ${error ? 'alert-danger' : 'alert-success'}`;
  window.scrollTo({top:0,behavior:'smooth'});
}
function intro(title, subtitle, action = '') {
  return `<div class="intro"><div><p class="eyebrow mb-2">REVENTA / MI NEGOCIO</p><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></div>${action}</div>`;
}
function table(data, columns, action) {
  if (!data.length) return '<div class="empty">No hay registros para mostrar. Crea uno nuevo o cambia los filtros.</div>';
  return `<div class="table-responsive"><table class="table"><thead><tr>${columns.map(k=>`<th scope="col">${esc(labels[k] || k)}</th>`).join('')}${action ? '<th scope="col">Acciones</th>' : ''}</tr></thead><tbody>${data.map(r=>`<tr>${columns.map(k=>`<td>${format(k,r[k])}</td>`).join('')}${action ? `<td><div class="actions">${action(r)}</div></td>`:''}</tr>`).join('')}</tbody></table></div>`;
}
function renderNav() {
  const links = [['dashboard','◫','Resumen'],['proveedores','◇','Proveedores'],['productos','▣','Productos'],['clientes','♧','Clientes'],['pedidos','▤','Pedidos'],['pagos','◉','Pagos'],['reportes','▥','Reportes']];
  if (admin()) links.push(['usuarios','○','Usuarios']);
  $('#navigation').innerHTML = links.map(([route,icon,title])=>`<a href="#${route}" data-nav="${route}"><span class="nav-icon" aria-hidden="true">${icon}</span>${title}</a>`).join('');
  $('#user-label').textContent = `${user.nombre} · ${admin() ? 'Administrador' : 'Vendedor'}`;
}
async function dashboard(version) {
  const result = await api('/dashboard');
  if(version !== loadVersion) return;
  view.innerHTML = intro('Resumen de tu negocio', 'Una mirada a tus ventas y pedidos, con información actualizada.') + `<div class="stats"><article class="stat primary"><div class="stat-label">Ventas del mes</div><div class="stat-value">${esc(money(result.ventas_mes))}</div><div class="stat-note">Valor de pedidos no cancelados</div></article><article class="stat"><div class="stat-label">Pedidos pendientes</div><div class="stat-value">${esc(result.pedidos_pendientes)}</div><div class="stat-note">Pedidos que requieren seguimiento</div></article><article class="stat"><div class="stat-label">Tu espacio</div><div class="stat-value">${admin() ? 'Equipo' : 'Mis ventas'}</div><div class="stat-note">${admin() ? 'Vista general del negocio' : 'Solo tus pedidos y pagos'}</div></article></div><section class="panel"><div class="panel-heading"><h2>Productos más vendidos</h2><a href="#pedidos" class="btn btn-sm btn-light">Ver pedidos →</a></div>${table(result.productos_mas_vendidos,['producto','unidades'])}</section><p class="subnote">Las ventas representan el valor de los pedidos, no el dinero recaudado. Se excluyen los pedidos cancelados.</p>`;
}
function resourceActions(key, record) {
  const cfg=resources[key], id=record[cfg.pk];
  let html = key === 'pedidos' ? `<a class="btn btn-sm btn-light" href="#pedido/${id}">Ver detalle</a>` : '';
  const canEdit = !['pagos','usuarios'].includes(key) || admin();
  const canDelete = key !== 'usuarios' && (!['proveedores','productos','clientes','pagos'].includes(key) || admin());
  if (canEdit) html += `<button class="btn btn-sm btn-outline-secondary" data-edit="${id}" data-resource="${key}">Editar</button>`;
  if (canDelete) html += `<button class="btn btn-sm btn-outline-danger" data-delete="${id}" data-resource="${key}">${key === 'pagos' ? 'Anular' : 'Eliminar'}</button>`;
  return html;
}
async function listResource(key, version) {
  if (key === 'usuarios' && !admin()) throw new Error('Se requiere rol administrador.');
  const cfg = resources[key]; activeResource=key;
  view.innerHTML = intro(cfg.title,cfg.subtitle,`<button class="btn btn-primary" data-new="${key}">+ Nuevo ${esc(cfg.singular)}</button>`) + `<section class="panel"><form id="filters" class="toolbar"></form><div id="results"><p class="empty">Cargando registros…</p></div></section>`;
  const filters=$('#filters');
  if(['productos','clientes','proveedores'].includes(key)) filters.innerHTML='<div class="search"><label for="q">Buscar por nombre</label><input class="form-control" id="q" name="q" placeholder="Escribe un nombre…" maxlength="100"></div>';
  if(['productos','proveedores'].includes(key)) filters.innerHTML+='<div><label for="activo">Estado</label><select class="form-select" name="activo" id="activo"><option value="">Todos</option><option value="1">Activo</option><option value="0">Inactivo</option></select></div>';
  if(['pedidos','pagos'].includes(key)) filters.innerHTML=`<div><label for="estado">Estado</label><select class="form-select" id="estado" name="estado"><option value="">Todos</option>${(key==='pedidos'?states:['REGISTRADO','ANULADO']).map(s=>`<option>${s}</option>`).join('')}</select></div><div><label for="filter-id">${key==='pedidos'?'ID de cliente':'ID de pedido'}</label><input type="number" min="1" step="1" class="form-control" id="filter-id" name="${key==='pedidos'?'id_cliente':'id_pedido'}"></div>`;
  if (filters.innerHTML) filters.innerHTML+='<button class="btn btn-outline-secondary" type="submit">Aplicar filtros</button><button class="btn btn-light" type="reset">Limpiar</button>';
  else filters.hidden=true;
  let requestVersion=0;
  const load = async () => {
    const request=++requestVersion;
    const params=new URLSearchParams();
    for(const [k,v] of new FormData(filters)) if(v.trim()) params.set(k,v.trim());
    try {
      const result=await api('/'+(cfg.endpoint || key)+'?'+params);
      if(version !== loadVersion || request !== requestVersion) return;
      records=result;
      $('#results').innerHTML=table(records,cfg.columns,r=>resourceActions(key,r));
    } catch(error) {if(version===loadVersion && request===requestVersion) {$('#results').innerHTML='<p class="empty">No se pudieron cargar los registros.</p>';notify(error.message,true);}}
  };
  filters.onsubmit=event=>{event.preventDefault();load();};
  filters.onreset=()=>setTimeout(load,0);
  await load();
}
async function orderView(id, version) {
  const result=await api('/pedidos/'+id);
  if(version !== loadVersion) return;
  const editable=!['CANCELADO','ENTREGADO'].includes(result.estado) && Number(result.pagado)===0;
  view.innerHTML=intro(`Pedido #${id}`,`${result.cliente} · ${result.estado}`, '<a class="btn btn-light" href="#pedidos">← Volver</a>')+`<section class="panel mb-4"><div class="detail-summary"><div><span>Total</span><strong>${esc(money(result.total))}</strong></div><div><span>Pagado</span><strong>${esc(money(result.pagado))}</strong></div><div><span>Saldo</span><strong>${esc(money(result.saldo))}</strong></div></div></section><section class="panel mb-4"><div class="panel-heading"><h2>Productos del pedido</h2>${editable?`<button class="btn btn-sm btn-primary" data-new="detalles" data-order="${id}">+ Agregar producto</button>`:''}</div>${table(result.detalles,resources.detalles.columns,editable?r=>resourceActions('detalles',r):null)}</section><section class="panel"><div class="panel-heading"><h2>Historial de pagos</h2>${result.estado!=='CANCELADO' && Number(result.saldo)>0?`<button class="btn btn-sm btn-primary" data-new="pagos" data-order="${id}">+ Registrar pago</button>`:''}</div>${table(result.pagos,['id_pago','monto','metodo','estado'],admin()?r=>resourceActions('pagos',r):null)}</section><p class="subnote">La existencia se reserva al agregar productos. Para cambiar productos de un pedido con pagos, primero anula sus pagos. Un pedido cancelado o entregado queda cerrado.</p>`;
  records=[...result.detalles,...result.pagos];
}
async function reportsView(version) {
  view.innerHTML=intro('Reportes','Consulta ventas consolidadas para conocer tu negocio.')+`<section class="panel"><form id="report-form" class="toolbar"><div><label for="report-kind">Reporte</label><select id="report-kind" class="form-select"><option value="ventas-cliente">Ventas por cliente</option><option value="ventas-proveedor">Ventas por proveedor</option><option value="ventas-periodo">Ventas por período</option></select></div><div id="date-from" hidden><label for="desde">Desde</label><input type="date" id="desde" class="form-control"></div><div id="date-to" hidden><label for="hasta">Hasta</label><input type="date" id="hasta" class="form-control"></div><button class="btn btn-primary">Consultar</button></form><div id="report-results"></div></section>`;
  const now=new Date(), localDate=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  $('#desde').value=localDate(new Date(now.getFullYear(),now.getMonth(),1));$('#hasta').value=localDate(now);
  $('#report-kind').onchange=()=>{const period=$('#report-kind').value==='ventas-periodo';$('#date-from').hidden=!period;$('#date-to').hidden=!period;$('#desde').required=period;$('#hasta').required=period;};
  let requestVersion=0;
  const load=async()=>{
    const request=++requestVersion;
    const kind=$('#report-kind').value;
    let query='';
    if(kind==='ventas-periodo') {
      if(!$('#desde').value || !$('#hasta').value || $('#desde').value>$('#hasta').value) return notify('Selecciona un intervalo de fechas válido.',true);
      query='?'+new URLSearchParams({desde:$('#desde').value,hasta:$('#hasta').value});
    }
    try {
      const data=await api('/reportes/'+kind+query);
      if(version!==loadVersion || request!==requestVersion)return;
      $('#report-results').innerHTML=table(data,kind==='ventas-cliente'?['nombre','pedidos','ventas']:kind==='ventas-proveedor'?['proveedor','ventas']:['periodo','pedidos','ventas']);
    }catch(error){if(version===loadVersion && request===requestVersion) notify(error.message,true);}
  };
  $('#report-form').onsubmit=event=>{event.preventDefault();load();};await load();
}
async function openEditor(key, record = {}, orderId) {
  const cfg=resources[key];
  formState={key,id:record[cfg.pk]};
  let fields=cfg.fields.map(f=>({...f}));
  if(key==='usuarios' && !formState.id) fields=[...fields.filter(f=>!['rol','activo'].includes(f.name)),field('contrasena','Contraseña inicial','password',{required:true,min:8,max:72})];
  $('#editor-title').textContent=`${formState.id?'Editar':'Nuevo'} ${cfg.singular}`;
  $('#form-error').hidden=true;
  const inputs=[];
  for(const f of fields) {
    let value=record[f.name] ?? f.value ?? '';
    if(f.name==='id_pedido' && orderId) value=orderId;
    const locked=(['detalles','pagos'].includes(key) && f.name==='id_pedido' && (orderId || formState.id)) || (key==='pedidos' && !formState.id && f.name==='estado');
    const attrs=`id="field-${f.name}" name="${f.name}" ${f.required?'required':''} ${locked?'disabled':''}`;
    let control;
    if(f.type==='select') {
      let options=f.options;
      if(f.source) {
        const list=await api('/'+f.source);
        const pk=resources[f.source].pk;
        options=list.map(row=>[row[pk],f.source==='pedidos'?`#${row[pk]} · ${row.cliente} · ${row.estado}`:row.nombre]);
      }
      control=`<select class="form-select" ${attrs}>${f.required?'<option value="">Seleccionar…</option>':''}${options.map(([v,l])=>`<option value="${esc(v)}" ${String(v)===String(value)?'selected':''}>${esc(l)}</option>`).join('')}</select>`;
    }else {
      const numeric=f.type==='number';
      control=`<input class="form-control" type="${f.type}" ${attrs} value="${esc(value)}" ${f.min!==undefined?`${numeric?'min':'minlength'}="${f.min}"`:''} ${f.max!==undefined?`${numeric?'max':'maxlength'}="${f.max}"`:''} ${numeric?`step="${f.step || 1}"`:''} ${f.type==='password'?'autocomplete="new-password"':''}>`;
    }
    inputs.push(`<div class="col-12 col-sm-6"><label class="form-label" for="field-${f.name}">${esc(f.label)}${f.required?' *':''}</label>${control}</div>`);
  }
  if(key==='productos') inputs.push('<p class="subnote">El precio de venta se calcula al guardar. La existencia es la cantidad disponible; cambia este valor solo para registrar un ajuste físico.</p>');
  if(key==='usuarios' && !formState.id) inputs.push('<p class="subnote">La cuenta nueva será VENDEDOR. Después puedes editar su rol.</p>');
  $('#fields').innerHTML=inputs.join('');
  formState.fields=fields;
  $('#editor').showModal();
}
$('#edit-form').onsubmit=async event=>{
  event.preventDefault();
  const {key,id,fields}=formState,cfg=resources[key],data={};
  for(const f of fields) {
    const input=$('#field-'+f.name),value=input.value;
    data[f.name]=value===''?(f.type==='number'?null:null):f.type==='number'||f.numeric?Number(value):value;
  }
  const button=$('#save-button');button.disabled=true;$('#form-error').hidden=true;
  try {
    let endpoint=cfg.endpoint || key;
    if(key==='usuarios' && !id) endpoint='auth/admin/usuarios';
    await api('/'+endpoint+(id?'/'+id:''),id?'PUT':'POST',data);
    $('#editor').close();await route();notify('Registro guardado correctamente.');
  }catch(error){$('#form-error').textContent=error.message;$('#form-error').hidden=false;}
  finally{button.disabled=false;}
};
$('#close-editor').onclick=$('#cancel-editor').onclick=()=>$('#editor').close();
view.addEventListener('click',async event=>{
  const button=event.target.closest('[data-new],[data-edit],[data-delete]');if(!button)return;
  try {
    if(button.dataset.new) return await openEditor(button.dataset.new,{},button.dataset.order?Number(button.dataset.order):undefined);
    const key=button.dataset.resource,cfg=resources[key],id=Number(button.dataset.edit || button.dataset.delete);
    if(button.dataset.edit) {
      const record=key==='usuarios'?records.find(r=>r[cfg.pk]===id):await api('/'+(cfg.endpoint||key)+'/'+id);
      return await openEditor(key,record);
    }
    if(!confirm(key==='pagos'?'¿Anular este pago? Se conservará el historial.':'¿Eliminar este registro? Esta acción no se puede deshacer.'))return;
    await api('/'+(cfg.endpoint||key)+'/'+id,'DELETE');await route();notify(key==='pagos'?'Pago anulado correctamente.':'Registro eliminado correctamente.');
  }catch(error){notify(error.message,true);}
});
async function route() {
  const version=++loadVersion,hash=location.hash.slice(1)||'dashboard';
  $('#message').hidden=true;
  document.querySelectorAll('[data-nav]').forEach(link=>link.classList.toggle('active',link.dataset.nav===(hash.startsWith('pedido/')?'pedidos':hash)));
  $('#breadcrumb').textContent=resources[hash]?.title || (hash.startsWith('pedido/')?'Detalle de pedido':hash==='reportes'?'Reportes':'Resumen');
  view.innerHTML='<p class="empty">Cargando información…</p>';
  try{
    if(hash==='dashboard')await dashboard(version);
    else if(hash==='reportes')await reportsView(version);
    else if(/^pedido\/\d+$/.test(hash))await orderView(Number(hash.split('/')[1]),version);
    else if(resources[hash] && hash!=='detalles')await listResource(hash,version);
    else {location.hash='dashboard';return;}
  }catch(error){if(version===loadVersion){view.innerHTML='<div class="panel empty">No fue posible cargar esta sección. <a href="#dashboard">Volver al resumen</a></div>';notify(error.message,true);}}
}
$('#logout').onclick=()=>{session.clear();location.href='login.html';};
window.addEventListener('hashchange',route);
(async()=>{
  if(!session.token()){location.href='login.html';return;}
  try{user=await api('/auth/me');renderNav();await route();}
  catch(error){notify(error.message,true);}
})();
