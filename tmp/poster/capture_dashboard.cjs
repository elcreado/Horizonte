const {chromium}=require('C:/Users/elcre/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {spawn,spawnSync}=require('child_process');
const path=require('path'); const crypto=require('crypto');
(async()=>{
const base=process.cwd();
const password=crypto.randomBytes(24).toString('hex');
const env={...process.env,PYTHONPATH:path.join(base,'backend')+';'+path.join(base,'tmp/poster'),DJANGO_SETTINGS_MODULE:'poster_settings',DEMO_PASSWORD:password,DJANGO_LOCAL_WORKER:'0',DJANGO_DEBUG:'1'};
delete env.POSTGRES_HOST;
for(const command of ['migrate','seed_demo']){
const r=spawnSync(path.join(base,'.venv/Scripts/python.exe'),['backend/manage.py',command,'--settings=poster_settings'],{env,encoding:'utf8',windowsHide:true});
if(r.status!==0) throw new Error(r.stderr); console.log(command+' complete');
}
const reset=spawnSync(path.join(base,'.venv/Scripts/python.exe'),['backend/manage.py','shell','--settings=poster_settings','-c',"import os; from django.contrib.auth import get_user_model; u=get_user_model().objects.get(username='demo'); u.set_password(os.environ['DEMO_PASSWORD']); u.save()"],{env,encoding:'utf8',windowsHide:true});
if(reset.status!==0) throw new Error(reset.stderr);
const backend=spawn(path.join(base,'.venv/Scripts/python.exe'),['backend/manage.py','runserver','127.0.0.1:8000','--noreload','--settings=poster_settings'],{env,stdio:'ignore',windowsHide:true});
const server=spawn(process.execPath,['frontend/node_modules/vite/bin/vite.js','frontend','--host','127.0.0.1','--port','5188'],{stdio:'ignore',windowsHide:true});
let browser;
try{
await new Promise(r=>setTimeout(r,3000));
browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const page=await browser.newPage({viewport:{width:1440,height:1080},deviceScaleFactor:1.5});
await page.goto('http://127.0.0.1:5188/#/login');
await page.locator('input[name="username"]').fill('demo');
await page.locator('input[name="password"]').fill(password);
await page.getByRole('button',{name:'Ingresar',exact:true}).click();
await page.getByText('La trayectoria de tu caja',{exact:true}).waitFor();
await page.waitForTimeout(1500);
await page.screenshot({path:'tmp/poster/dashboard-pc.png'});
await page.setViewportSize({width:430,height:932}); await page.waitForTimeout(800);
await page.screenshot({path:'tmp/poster/dashboard-mobile-full.png',fullPage:true});
await page.locator('.dashboard-content').screenshot({path:'tmp/poster/dashboard-mobile.png'});
await page.locator('.cards article').last().evaluate(el=>window.scrollTo(0,el.getBoundingClientRect().top+window.scrollY-16));
await page.screenshot({path:'tmp/poster/dashboard-mobile-focus.png'});
console.log('Dashboard real captured with isolated synthetic database');
}finally{if(browser) await browser.close(); server.kill(); backend.kill();}
})();
