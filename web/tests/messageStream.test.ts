import { afterEach, describe, expect, it, vi } from "vitest";
import { sendMessage } from "../src/api/client";

afterEach(() => vi.unstubAllGlobals());
function respond(body: string) {
  const fetch = vi.fn().mockResolvedValue(new Response(body, { status: 200 }));
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("message stream", () => {
  it("rejects EOF after partial events without a terminal response", async () => {
    respond('event: token\ndata: {"text":"Partial"}\n\n');
    const receive = vi.fn();
    await expect(sendMessage("conversation", "Hello", null, receive)).rejects.toThrow("interrupted");
    expect(receive).toHaveBeenCalledWith({ type: "token", data: { text: "Partial" } });
  });

  it("sends the stable operation identity, original text and file", async () => {
    const fetch = respond('event: done\ndata: {"status":"collecting","claim_id":"claim"}\n\n');
    const file = new File(["sample"], "sample.pdf", { type: "application/pdf" });
    await sendMessage("conversation", "Original text", file, vi.fn(), "en", "operation");
    const form = fetch.mock.calls[0][1].body as FormData;
    expect(form.get("operation_id")).toBe("operation");
    expect(form.get("text")).toBe("Original text");
    expect(form.get("file")).toBe(file);
  });

  it("accepts a terminal error so the reducer can display a retry action", async () => {
    respond('event: error\ndata: {"message":"Please retry"}\n\n');
    const receive = vi.fn();
    await sendMessage("conversation", "Hello", null, receive);
    expect(receive).toHaveBeenCalledWith({ type: "error", data: { message: "Please retry" } });
  });
});
