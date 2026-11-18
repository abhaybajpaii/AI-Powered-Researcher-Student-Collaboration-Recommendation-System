import { apiClient } from './client';
import { EvaluationBenchmarkResponse } from '../types';

export const evaluationApi = {
  benchmark: async (k: number = 5): Promise<EvaluationBenchmarkResponse> => {
    return apiClient<EvaluationBenchmarkResponse>(`/evaluation/benchmark?k=${k}`, {
      method: 'POST',
    });
  },

  runBenchmark: async (
    benchmarkSuite: string = 'standard_eval_v1',
    kValues: string = '5,10'
  ): Promise<EvaluationBenchmarkResponse> => {
    return apiClient<EvaluationBenchmarkResponse>(
      `/evaluation/benchmark?benchmark_suite=${encodeURIComponent(benchmarkSuite)}&k_values=${encodeURIComponent(kValues)}`,
      { method: 'POST' }
    );
  },
};
