const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('collab_token');
  
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 204) {
      return {} as T;
    }

    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      const errorMessage =
        (typeof data === 'object' && (data?.detail || data?.message)) ||
        `Request failed with status ${response.status}`;
      throw new ApiError(response.status, errorMessage, data);
    }

    return data as T;
  } catch (error: any) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(0, error.message || 'Network connection error');
  }
}

apiClient.get = <T>(endpoint: string, options: RequestInit = {}): Promise<T> =>
  apiClient<T>(endpoint, { ...options, method: 'GET' });

apiClient.post = <T>(endpoint: string, body?: any, options: RequestInit = {}): Promise<T> =>
  apiClient<T>(endpoint, {
    ...options,
    method: 'POST',
    body: body instanceof FormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });

apiClient.put = <T>(endpoint: string, body?: any, options: RequestInit = {}): Promise<T> =>
  apiClient<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: body instanceof FormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });

apiClient.delete = <T>(endpoint: string, options: RequestInit = {}): Promise<T> =>
  apiClient<T>(endpoint, { ...options, method: 'DELETE' });
