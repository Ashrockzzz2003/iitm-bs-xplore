import { API_URL, AGENT_APP_NAME } from '../constants';
import { ADKEvent } from '../types';

export interface SessionData {
  userId: string;
  sessionId: string;
  appName: string;
}

export interface AgentRunRequest {
  app_name: string;
  user_id: string;
  session_id: string;
  new_message: {
    role: string;
    parts: Array<{ text: string }>;
  };
  streaming?: boolean;
  state_delta?: Record<string, any>;
}

/**
 * Creates a session using the ADK session endpoint
 * Sessions are often auto-created, so this is optional but recommended
 */
export const createSession = async (sessionId: string, userId: string = "web-user"): Promise<SessionData> => {
  // Try the standard ADK session endpoint format
  const endpoint = `${API_URL}/apps/${AGENT_APP_NAME}/users/${userId}/sessions/${sessionId}`;
  
  console.log('Creating session at:', endpoint);

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      try {
        const data = await response.json();
        return {
          userId: data.userId || userId,
          sessionId: data.id || data.sessionId || sessionId,
          appName: data.appName || AGENT_APP_NAME
        };
      } catch (e) {
        // If response is not JSON, assume success and return the provided values
        return {
          userId,
          sessionId,
          appName: AGENT_APP_NAME
        };
      }
    } else {
      const errorText = await response.text();
      console.warn(`Session creation returned ${response.status}: ${errorText}`);
      
      // If 409 (Conflict), it means session already exists, which is treated as success
      if (response.status === 409) {
        return {
          userId,
          sessionId,
          appName: AGENT_APP_NAME
        };
      }
      
      throw new Error(`Failed to create session: ${response.status} ${errorText}`);
    }
  } catch (error) {
    // If session endpoint doesn't exist or fails, sessions are likely auto-created
    // Return the session data - it will work on first message
    console.error('Session creation endpoint error:', error);
    throw error;
  }
};

/**
 * Retry function with exponential backoff
 */
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 5,
  maxDuration: number = 30000 // 30 seconds
): Promise<T> => {
  const startTime = Date.now();
  let lastError: Error;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    if (Date.now() - startTime > maxDuration) {
      throw new Error(`Retry timeout after ${maxDuration}ms`);
    }

    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      const delay = Math.min(1000 * Math.pow(2, attempt), 5000); // Exponential backoff, max 5s
      if (attempt < maxRetries - 1) {
        console.log(`Attempt ${attempt + 1} failed, retrying in ${delay}ms...`, error);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError!;
};

export const streamMessage = async function* (
  query: string,
  sessionId: string,
  userId: string = "web-user"
): AsyncGenerator<ADKEvent, void, unknown> {
  
  const fetchRun = async () => {
    return await fetch(`${API_URL}/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        app_name: AGENT_APP_NAME,
        user_id: userId,
        session_id: sessionId,
        new_message: {
          role: "user",
          parts: [{ text: query }]
        },
        streaming: false
      }),
    });
  };

  let response = await fetchRun();

  if (!response.ok) {
    // Clone response to read text without consuming if we need to return it (though we re-fetch on retry)
    // Actually we can just read it, if we retry we get a new response.
    const errorText = await response.text();
    let isSessionError = false;
    
    try {
      const errorJson = JSON.parse(errorText);
      if (errorJson.detail === "Session not found") {
        isSessionError = true;
      }
    } catch (e) {
      // If not JSON, check text content
    }
    
    if (!isSessionError && errorText.includes("Session not found")) {
      isSessionError = true;
    }

    if (isSessionError) {
      console.log("Session not found, attempting to create session...");
      try {
        await createSession(sessionId, userId);
        console.log("Session created, retrying run...");
        response = await fetchRun();
      } catch (e) {
        console.error("Failed to auto-create session on retry:", e);
        // Throw the original error or the new one? 
        // Let's fall through to standard error handling with the original response if retry failed, 
        // BUT we need to reconstruct the error from the first response if we didn't update 'response'.
        // If createSession failed, we should probably throw that error or the original session not found error.
        throw new Error(`Session not found and failed to create new session: ${(e as Error).message}`);
      }
    } else {
       // For other errors, we need to throw.
       // Since we consumed the body, we must construct the error here using 'errorText'.
       let errorMessage = `Server error: ${response.status} ${response.statusText}`;
        try {
          if (errorText) {
            try {
              const errorJson = JSON.parse(errorText);
              if (errorJson.detail) {
                errorMessage = errorJson.detail;
              } else if (errorJson.message) {
                errorMessage = errorJson.message;
              } else {
                errorMessage = errorText;
              }
            } catch {
              if (errorText.trim()) {
                errorMessage = errorText;
              }
            }
          }
          
          if (response.status === 404) {
            errorMessage = `Endpoint not found (404). Please check if the backend server is running and the endpoint '/run' is available.`;
          } else if (response.status === 500) {
            errorMessage = errorMessage || 'Internal server error. Please try again later.';
          }
        } catch (e) {
           // ignore
        }
        throw new Error(errorMessage);
    }
  }
  
  // If we retried, response is the new response. Check it again.
  if (!response.ok) {
     // This handles the case where retry also failed (e.g. 404 again)
    let errorMessage = `Server error: ${response.status} ${response.statusText}`;
    try {
      const errorText = await response.text();
      if (errorText) {
        try {
          const errorJson = JSON.parse(errorText);
          if (errorJson.detail) {
            errorMessage = errorJson.detail;
          } else if (errorJson.message) {
            errorMessage = errorJson.message;
          } else {
            errorMessage = errorText;
          }
        } catch {
          if (errorText.trim()) {
            errorMessage = errorText;
          }
        }
      }
      
      if (response.status === 404) {
        // Could be session not found AGAIN or endpoint not found
         errorMessage = `Endpoint not found (404) or Session creation failed. ${errorMessage}`;
      } else if (response.status === 500) {
        errorMessage = errorMessage || 'Internal server error. Please try again later.';
      }
    } catch (e) {
        if (response.status === 404) {
            errorMessage = 'Endpoint not found (404).';
        }
    }
    throw new Error(errorMessage);
  }

  const events: ADKEvent[] = await response.json();
  
  for (const event of events) {
    yield event;
  }
};
