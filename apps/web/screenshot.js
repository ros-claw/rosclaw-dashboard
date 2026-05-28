const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: '/home/ubuntu/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome',
    headless: true
  });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1
  });
  await page.goto('http://127.0.0.1:3002', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  await page.evaluate(() => {
    document.querySelectorAll('video, canvas').forEach(el => el.remove());
  });
  await page.screenshot({
    path: '/home/ubuntu/rosclaw/rosclaw_dashboard/dashboard-screenshot.png',
    fullPage: false,
    timeout: 60000,
    type: 'png'
  });
  console.log('Screenshot saved to dashboard-screenshot.png');
  await browser.close();
})();
