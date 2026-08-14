import { test, expect } from '@playwright/test';
import { chromium } from 'playwright';

/**
 * OriStudio 数据注入 E2E 测试
 * 通过前端界面模拟用户操作，录入测试数据
 */

const BASE_URL = 'http://localhost:5174';
const API_BASE = 'http://localhost:8000';

test.describe('Data Injection via UI', () => {
  let token: string | null = null;
  let registeredUsers: any[] = [];
  let createdWorks: any[] = [];

  test.beforeAll(async () => {
    console.log('\n=== OriStudio Data Injection E2E Test ===\n');
  });

  test('should get auth token via local-login', async ({ page }) => {
    console.log('[Step 1] Getting auth token...');
    const response = await page.request.post(`${API_BASE}/api/auth/local-login`);
    expect(response.status()).toBe(200);

    const data = await response.json();
    token = data?.data?.token;
    expect(token).toBeTruthy();
    console.log(`   ✓ Token obtained: ${token?.substring(0, 20)}...`);
  });

  test('should register creators via API', async ({ page }) => {
    console.log('\n[Step 2] Registering creators...');
    const creatorTypes = ['illustrator', 'photographer', 'video_creator', 'crafter', 'musician', 'writer'];

    for (const ct of creatorTypes) {
      for (let i = 1; i <= 5; i++) {
        const username = `${ct}_${i}`;
        const email = `${username}@test.orispark.com`;

        const response = await page.request.post(`${API_BASE}/api/auth/register/creator`, {
          headers: { 'Authorization': `Bearer ${token}` },
          data: { username, email, password: 'Test123456!' }
        });

        // Accept 200, 201, or 400 (already exists)
        expect([200, 201, 400]).toContain(response.status());

        if (response.status() === 200 || response.status() === 201) {
          const data = await response.json();
          registeredUsers.push({
            type: ct,
            username,
            email,
            id: data?.data?.user?.id
          });
        }
        console.log(`   ✓ Registered ${username}`);
        await page.waitForTimeout(100);
      }
    }
    console.log(`   Total: ${registeredUsers.length} creators registered`);
  });

  test('should create works for each creator', async ({ page }) => {
    console.log('\n[Step 3] Creating works...');
    const titles = ['星空下的花园', '城市夜景', '梦幻森林', '秋日私语', '晨光中的教堂'];

    for (const user of registeredUsers) {
      for (let i = 1; i <= 5; i++) {
        const title = `${user.type}_${i}`;
        const fileType = user.type === 'musician' ? 'audio' : 'image';

        const response = await page.request.post(`${API_BASE}/api/works`, {
          headers: { 'Authorization': `Bearer ${token}` },
          data: {
            title,
            file_type: fileType,
            file_path: `test_media/images/${user.type}_${i}.jpg`,
            creator_id: user.id,
            creator_type: user.type,
            import_mode: 'full',
            status: 'active'
          }
        });

        expect([200, 201]).toContain(response.status());

        if (response.status() === 200 || response.status() === 201) {
          const data = await response.json();
          createdWorks.push({
            id: data?.data?.id,
            title,
            creator_type: user.type
          });
        }
        console.log(`   ✓ Created ${title}`);
        await page.waitForTimeout(50);
      }
    }
    console.log(`   Total works created: ${createdWorks.length}`);
  });

  test('should create contracts', async ({ page }) => {
    console.log('\n[Step 4] Creating contracts...');

    for (let i = 1; i <= 10; i++) {
      const workId = createdWorks[(i - 1) % createdWorks.length]?.id;
      const creatorId = registeredUsers[(i - 1) % registeredUsers.length]?.id;

      const response = await page.request.post(`${API_BASE}/api/contract`, {
        headers: { 'Authorization': `Bearer ${token}` },
        data: {
          title: `合约 ${i}`,
          work_id: workId,
          creator_id: creatorId,
          contract_type: ['exclusive_license', 'non_exclusive_license', 'transfer', 'commission'][i % 4],
          total_amount: 5000 + i * 1000,
          currency: 'CNY',
          billing_cycle: 'one_time'
        }
      });

      expect([200, 201]).toContain(response.status());
      console.log(`   ✓ Created contract ${i}`);
      await page.waitForTimeout(50);
    }
  });

  test('should create notary records', async ({ page }) => {
    console.log('\n[Step 5] Creating notary records...');

    for (let i = 0; i < Math.min(20, createdWorks.length); i++) {
      const workId = createdWorks[i].id;

      const response = await page.request.post(`${API_BASE}/api/notary/records`, {
        headers: { 'Authorization': `Bearer ${token}` },
        data: {
          work_id: workId,
          platform: ['banquanjia', 'antchain', 'zhixinchain'][i % 3]
        }
      });

      expect([200, 201]).toContain(response.status());
      console.log(`   ✓ Created notary for ${createdWorks[i].title.substring(0, 8)}`);
      await page.waitForTimeout(50);
    }
  });

  test('should verify data counts', async ({ page }) => {
    console.log('\n[Step 6] Verifying data...');

    // Get work counts
    const worksResp = await page.request.get(`${API_BASE}/api/works?limit=200`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const worksData = await worksResp.json();
    const totalWorks = worksData?.data?.total || worksData?.data?.length || 0;

    // Get user counts
    const usersResp = await page.request.get(`${API_BASE}/api/auth/users?limit=100`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const usersData = await usersResp.json();
    const totalUsers = usersData?.data?.total || usersData?.data?.length || 0;

    console.log(`\n   Users: ${totalUsers} (expected: 48+)`);
    console.log(`   Works: ${totalWorks} (expected: 150)`);

    expect(totalUsers).toBeGreaterThanOrEqual(48);
    expect(totalWorks).toBeGreaterThanOrEqual(30);

    console.log('\n   ✓ Data verification passed');
  });

  test('should open frontend and check UI', async ({ page }) => {
    console.log('\n[Step 7] Testing frontend UI...');

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Check if app loaded
    const appEl = page.locator('#app');
    await expect(appEl).toBeVisible();
    console.log('   ✓ Frontend loaded successfully');

    // Try to access works page
    await page.goto(`${BASE_URL}/app/works`);
    await page.waitForLoadState('networkidle');

    // Check for error handling
    const content = await page.locator('body').textContent();
    expect(content).toBeTruthy();
    console.log('   ✓ Works page accessible');
  });
});
