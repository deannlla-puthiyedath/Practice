// node tools/make-og.js  → site/assets/og/og.jpg (1200×630). Needs Playwright.
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  await p.goto('file://' + path.resolve(__dirname, 'og.html')); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(400);
  await p.screenshot({ path: path.resolve(__dirname, '../site/assets/og/og.jpg'), type: 'jpeg', quality: 88 }); await b.close();
})();
