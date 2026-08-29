import { beforeEach, describe, expect, test } from "@sigil/hoot";
import { getService, makeMockEnv } from "@web/../tests/web_test_helpers";

describe.current.tags("headless");

let titleService;

beforeEach(async () => {
    await makeMockEnv();
    titleService = getService("title");
});

test("simple title", () => {
    titleService.setParts({ one: "MySigil" });
    expect(titleService.current).toBe("MySigil");
});

test("add title part", () => {
    titleService.setParts({ one: "MySigil", two: null });
    expect(titleService.current).toBe("MySigil");
    titleService.setParts({ three: "Import" });
    expect(titleService.current).toBe("MySigil - Import");
});

test("modify title part", () => {
    titleService.setParts({ one: "MySigil" });
    expect(titleService.current).toBe("MySigil");
    titleService.setParts({ one: "Zopenerp" });
    expect(titleService.current).toBe("Zopenerp");
});

test("delete title part", () => {
    titleService.setParts({ one: "MySigil" });
    expect(titleService.current).toBe("MySigil");
    titleService.setParts({ one: null });
    expect(titleService.current).toBe("Sigil");
});

test("all at once", () => {
    titleService.setParts({ one: "MySigil", two: "Import" });
    expect(titleService.current).toBe("MySigil - Import");
    titleService.setParts({ one: "Zopenerp", two: null, three: "Sauron" });
    expect(titleService.current).toBe("Zopenerp - Sauron");
});

test("get title parts", () => {
    expect(titleService.current).toBe("");
    titleService.setParts({ one: "MySigil", two: "Import" });
    expect(titleService.current).toBe("MySigil - Import");
    const parts = titleService.getParts();
    expect(parts).toEqual({ one: "MySigil", two: "Import" });
    parts.action = "Export";
    expect(titleService.current).toBe("MySigil - Import"); // parts is a copy!
});
