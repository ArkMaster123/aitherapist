
# Tool Calling Debug Documentation

## Problem Summary

The application successfully connects to the vLLM server and receives responses, but the model is **not calling the `generate_ascii_art` tool** when users express sadness, despite:
- Tool calling being enabled on the vLLM server (`--enable-auto-tool-choice` and `--tool-call-parser hermes`)
- Tools being configured in the API route
- The system prompt explicitly instructing the model to use the tool
- Direct API testing confirming tool calling works at the vLLM level

### Current Behavior
- ✅ User messages are received and processed
- ✅ Model responds with empathetic text
- ❌ Model does NOT call the `generate_ascii_art` tool when users express sadness
- ❌ ASCII art never appears in the UI

### Expected Behavior
- ✅ User says "I feel sad" or "make me some art"
- ✅ Model recognizes sadness/distress
- ✅ Model calls `generate_ascii_art` tool with appropriate theme
- ✅ Tool executes and returns ASCII art
- ✅ ASCII art displays in the terminal UI with a styled box

---

## What Has Been Attempted

### 1. Server Configuration Fixes
**Files Modified:**
- `scripts/vllm_server.py`

**Changes:**
- ✅ Added `--enable-auto-tool-choice` flag
- ✅ Added `--tool-call-parser hermes` (correct for Qwen2.5-7B-Instruct)
- ✅ Removed stray `"llm"` argument from command
- ✅ Redeployed server multiple times

**Result:** Server is correctly configured. Direct curl tests confirm tool calling works.

---

### 2. API Route Tool Configuration
**Files Modified:**
- `app/api/chat/route.ts`

**Changes:**
- ✅ Added tool definition using AI SDK v5's `tool()` function
- ✅ Configured tool to accept theme and optional message
- ✅ Added tool execution logic with ASCII art templates
- ✅ Enabled tools for all endpoints (not just OpenAI)
- ✅ Set `toolChoice: 'auto'`
- ✅ Increased `maxTokens` from 2000 to 4000
- ✅ Added `maxSteps: 5` to allow multiple tool call rounds

**Tool Definition:**
```typescript
const generateAsciiArt = tool({
  description: 'MANDATORY: Generate comforting ASCII art when user expresses sadness...',
  parameters: z.object({
    theme: z.enum(['happy', 'comfort', 'sun', 'heart', 'cat']),
    message: z.string().optional()
  }),
  execute: async ({ theme, message }) => { /* ... */ }
});
```

**Result:** Tools are configured, but model doesn't call them.

---

### 3. System Prompt Improvements
**Files Modified:**
- `app/api/chat/route.ts`

**Changes:**
- ✅ Made system prompt more directive about tool usage
- ✅ Changed from "you may use" to "CRITICAL: you MUST use"
- ✅ Added explicit examples: "I feel sad", "very sad", "make me some art"
- ✅ Specified theme recommendations ("comfort" or "heart" for sadness)

**Current System Prompt Excerpt:**
```
- CRITICAL: When a user expresses sadness, grief, distress, depression, or asks for art/comforting content, you MUST use the generate_ascii_art tool. Examples: "I feel sad", "very sad", "make me some art", "I'm depressed". Always call the tool with theme="comfort" or "heart" when users express negative emotions.
```

**Result:** More directive prompt, but model still doesn't call tool.

---

### 4. Message Processing Fixes
**Files Modified:**
- `app/api/chat/route.ts`

**Changes:**
- ✅ Simplified message processing to use `convertToModelMessages` directly
- ✅ Added proper handling for tool messages (vLLM requires string content)
- ✅ Fixed content array to string conversion for vLLM
- ✅ Added filtering to remove invalid empty messages
- ✅ Added logging to track message count and structure

**Issues Found:**
- Message count drops from 7 to 1 after processing (messages being lost)
- Empty assistant messages are being filtered out
- Tool results in `parts` array might not be properly extracted

**Current Processing Flow:**
1. UI messages → `convertToModelMessages()` 
2. Add system prompt if missing
3. Convert content arrays to strings for vLLM
4. Fix tool message content format
5. Filter invalid messages

**Result:** Messages are being processed but some are lost. Tool still not called.

---

### 5. Client-Side Component Updates
**Files Modified:**
- `components/terminal-chat.tsx`

**Changes:**
- ✅ Updated to handle AI SDK v5 message format with `parts` array
- ✅ Added tool result extraction from parts
- ✅ Added debug logging for tool calls and results
- ✅ Created special `ascii-art` display type
- ✅ Added styled box for ASCII art display

**Result:** UI is ready to display tool results, but tool is never called.

---

### 6. Error Handling Improvements
**Files Modified:**
- `app/api/chat/route.ts`
- `components/terminal-chat.tsx`

**Changes:**
- ✅ Added comprehensive error logging
- ✅ Added request/response logging
- ✅ Added tool call detection logging
- ✅ Improved error messages

**Logs Show:**
- Requests are received correctly
- Tools are configured (`hasTools: true`)
- Messages are processed
- Model responds but never calls tools

---

## Root Cause Analysis

### Possible Issues:

1. **AI SDK v5 + `createOpenAICompatible` Tool Handling**
   - The `createOpenAICompatible` provider might not properly handle tool execution loop
   - Tool calls might be detected but not automatically executed
   - Tool results might not be sent back to vLLM for final response

2. **Model Behavior**
   - Fine-tuned model might not be trained to use tools effectively
   - Model might prefer text responses over tool calls
   - Tool calling format might not match what the model expects

3. **Message Format Mismatch**
   - vLLM expects tool messages in a specific format
   - Tool call IDs might not match between calls and results
   - Content format for tool messages might be incorrect

4. **Tool Definition Format**
   - Tool schema might not match vLLM's expected format
   - Tool description might not be clear enough for the model
   - Parameter schema might need adjustment

---

## Files Impacted

### Modified Files:

1. **`scripts/vllm_server.py`**
   - Added `--enable-auto-tool-choice`
   - Added `--tool-call-parser hermes`
   - Removed stray `"llm"` argument
   - **Status:** ✅ Correctly configured, deployed

2. **`app/api/chat/route.ts`**
   - Added tool definition (`generateAsciiArt`)
   - Added system prompt with tool instructions
   - Updated message processing for tool handling
   - Added tool execution logic
   - Increased maxTokens and added maxSteps
   - **Status:** ⚠️ Configured but tool not being called

3. **`components/terminal-chat.tsx`**
   - Updated for AI SDK v5 message format
   - Added tool result extraction and display
   - Added ASCII art display styling
   - Added debug logging
   - **Status:** ✅ Ready to display results

4. **`components/terminal-output.tsx`**
   - Added `ascii-art` type
   - Added special styling for ASCII art
   - **Status:** ✅ Ready

5. **`env.example`**
   - Added `ENABLE_TOOLS` configuration option
   - **Status:** ✅ Documented

---

## Testing Performed

### 1. Direct vLLM API Test (✅ Works)
```bash
curl -X POST https://whataidea--vllm-therapist-serve.modal.run/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-therapist",
    "messages": [
      {"role": "user", "content": "I feel sad, make me some art"}
    ],
    "tools": [...],
    "tool_choice": "auto"
  }'
```
**Result:** ✅ vLLM returns tool call correctly

### 2. Application Integration Test (❌ Doesn't Work)
- User sends "i feel sad" in browser
- **Result:** Model responds with text but doesn't call tool

---

## Next Steps / Potential Solutions

### Option 1: Force Tool Choice
When detecting sadness keywords, set `toolChoice: 'required'` or force specific tool:
```typescript
// Detect sadness in user message
const lastUserMessage = messages[messages.length - 1];
const userText = extractTextFromMessage(lastUserMessage);
const hasSadness = /sad|depressed|down|art/i.test(userText);

if (hasSadness && enableTools) {
  streamOptions.toolChoice = {
    type: 'tool',
    toolName: 'generate_ascii_art'
  };
}
```

### Option 2: Manual Tool Execution
Instead of relying on AI SDK's automatic tool execution, manually handle the loop:
1. Send request to vLLM
2. Check if response has tool calls
3. Execute tools manually
4. Send tool results back
5. Get final response

### Option 3: Check AI SDK Compatibility
- Verify `createOpenAICompatible` fully supports tool calling
- Check if tool execution loop works with vLLM
- Consider using standard OpenAI provider to test if it's a compatibility issue

### Option 4: Model Training/Fine-tuning
- The fine-tuned model might need additional training on tool calling
- Verify the base model (Qwen2.5-7B-Instruct) supports tool calling with Hermes format
- Test with base model (not fine-tuned) to see if tool calling works

### Option 5: Tool Definition Format
- Try different tool description styles
- Verify parameter schema matches vLLM's expectations
- Check if tool name format matters

---

## Debugging Logs

### Key Log Outputs:

**Request Received:**
```
Messages count: 7
StreamText options: {
  "model": "qwen-therapist",
  "hasTools": true,
  "toolChoice": "auto",
  "messageCount": 1  // ⚠️ Should be more!
}
```

**vLLM Server Logs:**
```
POST /v1/chat/completions -> 200 OK
```
Server responds successfully but no tool calls in response.

---

## Related Documentation

- [AI SDK v5 Tool Calling Docs](https://v5.ai-sdk.dev/docs/foundations/tools)
- [vLLM Tool Calling Guide](https://docs.vllm.ai/en/latest/features/tool_calling.html)
- [Qwen Tool Calling Format](https://qwen.readthedocs.io/en/v2.0/framework/function_call.html)

---

## Status

**Current Status:** ✅ **Tool calling WORKING**

**Last Updated:** 2025-12-12

**Solution Implemented:**
1. Fixed AI SDK v5 compatibility - changed `parameters` to `inputSchema` in tool definition
2. Added forced tool calling when sadness keywords detected (`toolChoice: 'required'`)
3. Fixed UI to handle AI SDK v5 message format (`type: "tool-{toolName}"` with `output` property)
4. Added fallback message conversion to handle tool call responses in conversation history

**What Was Fixed:**
- Tool definition now uses correct AI SDK v5 `inputSchema` property
- Automatic sadness detection forces tool to be called via `toolChoice: 'required'`
- UI now correctly extracts and displays tool results from `parts` array
- Message conversion handles tool call responses to prevent errors in follow-up messages

