// File: frontend/src/services/rpcClient.js
// Description: Fast JSON-RPC 2.0 Client for accelerated operations and batch execution

const RPC_ENDPOINT = '/api/rpc/v1';

let requestIdCounter = 1;

export const rpcClient = {
  /**
   * Executes a single JSON-RPC method call
   */
  async call(method, params = {}) {
    const id = requestIdCounter++;
    const payload = {
      jsonrpc: '2.0',
      method,
      params,
      id
    };

    const response = await fetch(RPC_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`RPC transport failed: ${response.statusText}`);
    }

    const data = await response.json();
    if (data.error) {
      throw new Error(`RPC Error [${data.error.code}]: ${data.error.message}`);
    }

    return {
      result: data.result,
      executionTimeMs: data.execution_time_ms
    };
  },

  /**
   * Executes multiple JSON-RPC calls concurrently in a single network round-trip
   */
  async batchCall(calls = []) {
    const payload = calls.map(c => ({
      jsonrpc: '2.0',
      method: c.method,
      params: c.params || {},
      id: requestIdCounter++
    }));

    const response = await fetch(RPC_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Batch RPC transport failed: ${response.statusText}`);
    }

    return await response.json();
  }
};

