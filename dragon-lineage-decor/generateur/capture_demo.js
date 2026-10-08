const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({args:['--use-gl=swiftshader','--ignore-gpu-blocklist']});
  const p = await b.newPage({viewport:{width:1280,height:720}});
  p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('file://' + process.cwd() + '/dragon-cristal-demo.html');
  await p.waitForTimeout(5000);
  await p.click('[data-view=side]'); await p.waitForTimeout(800);
  await p.screenshot({path:'s1.png'});
  await p.click('[data-view=three]'); await p.waitForTimeout(800);
  await p.screenshot({path:'s2.png'});
  await b.close();
})();
