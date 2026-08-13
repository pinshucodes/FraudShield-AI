export const fetchApi = async (endpoint, options = {}) => {
  try {
    const token = localStorage.getItem('token');
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers,
    };

    const response = await fetch(`/api${endpoint}`, config);
    
    // Parse JSON
    const data = await response.json().catch(() => null);

    if (!response.ok) {
      // Create error object with response data
      const error = new Error(data?.detail || 'An error occurred with the request');
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
};
