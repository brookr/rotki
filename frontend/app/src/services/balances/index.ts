import { type ActionResult } from '@rotki/common/lib/data';
import { axiosSnakeCaseTransformer } from '@/services/axios-tranformers';
import { api } from '@/services/rotkehlchen-api';
import { type PendingTask } from '@/services/types-api';
import { handleResponse, validStatus } from '@/services/utils';
import { type AllBalancePayload } from '@/store/balances/types';

export const useBalancesApi = () => {
  const queryBalancesAsync = async (
    payload: Partial<AllBalancePayload>
  ): Promise<PendingTask> => {
    const response = await api.instance.get<ActionResult<PendingTask>>(
      '/balances',
      {
        params: axiosSnakeCaseTransformer({
          asyncQuery: true,
          ...payload
        }),
        validateStatus: validStatus
      }
    );
    return handleResponse(response);
  };

  return {
    queryBalancesAsync
  };
};
