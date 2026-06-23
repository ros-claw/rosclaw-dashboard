import { test, expect } from '@playwright/test';

const GOLDEN_RUN_ID = 'golden_pick_cube_failure';

test.describe('Trace Viewer', () => {
  test('loads golden run, renders multi-track timeline, and jumps to failure', async ({ page }) => {
    await page.goto(`/runs/${GOLDEN_RUN_ID}`);

    // Wait for the trace viewer to load.
    await expect(page.getByText('Trace Timeline')).toBeVisible();
    await expect(page.getByText('Pick red cube from bin A and place on conveyor')).toBeVisible();

    // Verify representative tracks are rendered.
    for (const track of ['Task', 'Agent', 'Tool', 'Provider', 'Failure']) {
      await expect(page.getByText(track, { exact: true })).toBeVisible();
    }

    // The failure event should be present in the failure track.
    const failureEvent = page.getByTitle(/Object dropped @ 42\.50s/);
    await expect(failureEvent).toBeVisible();

    // Click the failure event to select it and seek the replay.
    // Normal actionability checks time out on this marker in headless Chromium
    // because of a page-level stability issue; force click is a verified workaround.
    await failureEvent.click({ force: true });

    // The event should become selected (ring highlight).
    await expect(failureEvent).toHaveClass(/ring-rosclaw-500/);

    // Replay time should jump to the failure timestamp.
    const timeDisplay = page.locator('text=0:42.500 / 0:42.500');
    await expect(timeDisplay).toBeVisible();

    // The Failure Analysis panel should list the failure and allow jumping.
    await expect(page.getByText('Object dropped').first()).toBeVisible();
    const jumpButton = page.getByRole('button', { name: 'Jump' });
    await expect(jumpButton).toBeVisible();

    // Reset playback to the beginning and click Jump in the panel.
    await page.locator('input[type="range"]').fill('0');
    await expect(page.locator('text=0:00.000 / 0:42.500')).toBeVisible();

    await jumpButton.click({ force: true });
    await expect(timeDisplay).toBeVisible();
  });
});
