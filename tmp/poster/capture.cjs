const {chromium}=require('C:/Users/elcre/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
const server=require('child_process').spawn(process.execPath,['frontend/node_modules/vite/bin/vite.js','frontend','--host','127.0.0.1','--port','5188'],{stdio:'ignore',windowsHide:true});
await new Promise(r=>setTimeout(r,1800));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const page=await browser.newPage({viewport:{width:1440,height:950},deviceScaleFactor:1.5});
await page.goto('http://127.0.0.1:5188/'); await page.waitForTimeout(1300);
await page.screenshot({path:'tmp/poster/pc.png'});
await page.setViewportSize({width:390,height:844}); await page.screenshot({path:'tmp/poster/mobile.png'});
await browser.close(); server.kill(); console.log('captured');
})();
