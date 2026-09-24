// Run against the local app after scripts/seed_demo.py. No repository code is executed.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const path = require('path');
process.chdir(path.resolve(__dirname, '..'));
(async()=>{
  const browser = await chromium.launch({headless:true, channel:'chrome'});
  const page = await browser.newPage({viewport:{width:1440,height:1120},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:5173');
  await page.getByRole('button',{name:'Start review',exact:true}).waitFor();
  await page.screenshot({path:path.resolve('docs/dashboard.png'),fullPage:true});
  await page.getByRole('button',{name:'Review history',exact:true}).click();
  await page.getByRole('heading',{name:'synthetic/python_bad'}).first().waitFor();
  await page.getByRole('heading',{name:'synthetic/python_bad'}).first().click();
  await page.getByRole('heading',{name:'Review findings'}).waitFor();
  await page.getByText('Mutable default argument',{exact:true}).waitFor();
  await page.screenshot({path:path.resolve('docs/review.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.resolve('docs/review-mobile.png'),fullPage:true});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth > innerWidth);
  if(overflow) errors.push('Mobile horizontal overflow');
  if(process.argv.includes('--live')) {
    await page.setViewportSize({width:1440,height:1120});
    await page.getByRole('button',{name:'Repository reviews'}).click();
    await page.getByLabel('GitHub repository URL',{exact:false}).fill('https://github.com/pallets/itsdangerous');
    await page.getByRole('button',{name:'Start review',exact:true}).click();
    await page.getByRole('heading',{name:'pallets/itsdangerous',exact:true}).waitFor({timeout:30000});
    await page.getByRole('heading',{name:'Review findings'}).waitFor({timeout:120000});
    const identifier=new URL(page.url()).searchParams.get('review');
    const response=await fetch(`http://127.0.0.1:8000/api/reviews/${identifier}`);
    const review=await response.json();
    if(review.status !== 'completed') errors.push('Live review failed');
    const evidence={review_id:identifier,status:review.status,commit:review.report?.repository?.commit,
      event_count:review.events?.length,health:await (await fetch('http://127.0.0.1:8000/api/health')).json()};
    require('fs').writeFileSync(path.resolve('docs/ui-live-verification.json'),JSON.stringify(evidence,null,2));
    await page.screenshot({path:path.resolve('docs/live-dashboard.png'),fullPage:true});
  }
  await browser.close();
  console.log(JSON.stringify({browser:'Chrome',screenshots:3,pageErrors:errors,mobileOverflow:overflow}));
  if(errors.length) process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
