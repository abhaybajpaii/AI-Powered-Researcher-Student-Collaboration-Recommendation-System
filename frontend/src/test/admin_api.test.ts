import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiClientMock = vi.hoisted(() => vi.fn());

vi.mock('../api/client', () => ({ apiClient: apiClientMock }));

import { adminApi } from '../api/admin';

describe('admin API request contracts', () => {
  beforeEach(() => {
    apiClientMock.mockReset();
  });

  it('nests synthetic seed settings in the backend request schema', async () => {
    apiClientMock.mockResolvedValue({
      status: 'COMPLETED',
      job_id: 'job-1',
      records_processed: 10,
      records_created: 10,
      records_updated: 0,
    });

    await adminApi.seedSynthetic({
      num_students: 5,
      num_faculty: 5,
      num_publications: 10,
      seed: 42,
    });

    expect(apiClientMock).toHaveBeenCalledWith('/admin/seed-synthetic', {
      method: 'POST',
      body: JSON.stringify({
        config: {
          num_students: 5,
          num_faculty: 5,
          num_publications: 10,
          seed: 42,
        },
        reset_existing: false,
      }),
    });
  });
});
