interface RateLimitStatus {
  remaining: number;
  resetAt: Date | null;
}

const RATE_LIMIT_KEY = 'terminal_chat_rate_limit';
const MESSAGES_PER_DAY = 10;
const DAY_MS = 24 * 60 * 60 * 1000;

interface RateLimitData {
  messages: number[];
  resetAt: number;
}

export async function checkRateLimit(): Promise<RateLimitStatus> {
  if (typeof window === 'undefined') {
    // Server-side: use a server-side store (Redis, database, etc.)
    // For now, return default values
    return { remaining: MESSAGES_PER_DAY, resetAt: null };
  }

  const stored = localStorage.getItem(RATE_LIMIT_KEY);
  const now = Date.now();

  if (!stored) {
    return {
      remaining: MESSAGES_PER_DAY,
      resetAt: new Date(now + DAY_MS),
    };
  }

  const data: RateLimitData = JSON.parse(stored);

  // Check if we need to reset (past the reset time)
  if (now > data.resetAt) {
    // Reset the counter
    const newData: RateLimitData = {
      messages: [],
      resetAt: now + DAY_MS,
    };
    localStorage.setItem(RATE_LIMIT_KEY, JSON.stringify(newData));
    return {
      remaining: MESSAGES_PER_DAY,
      resetAt: new Date(now + DAY_MS),
    };
  }

  // Filter out messages older than 24 hours
  const dayAgo = now - DAY_MS;
  const recentMessages = data.messages.filter(timestamp => timestamp > dayAgo);

  // Update stored data
  const updatedData: RateLimitData = {
    messages: recentMessages,
    resetAt: data.resetAt,
  };
  localStorage.setItem(RATE_LIMIT_KEY, JSON.stringify(updatedData));

  const remaining = MESSAGES_PER_DAY - recentMessages.length;

  return {
    remaining: Math.max(0, remaining),
    resetAt: new Date(data.resetAt),
  };
}

export async function recordMessage(): Promise<void> {
  if (typeof window === 'undefined') {
    return;
  }

  const stored = localStorage.getItem(RATE_LIMIT_KEY);
  const now = Date.now();

  let data: RateLimitData;
  if (!stored) {
    data = {
      messages: [],
      resetAt: now + DAY_MS,
    };
  } else {
    data = JSON.parse(stored);
    
    // Reset if past reset time
    if (now > data.resetAt) {
      data = {
        messages: [],
        resetAt: now + DAY_MS,
      };
    }
  }

  // Add current message timestamp
  data.messages.push(now);
  
  // Filter out messages older than 24 hours
  const dayAgo = now - DAY_MS;
  data.messages = data.messages.filter(timestamp => timestamp > dayAgo);

  localStorage.setItem(RATE_LIMIT_KEY, JSON.stringify(data));
}

