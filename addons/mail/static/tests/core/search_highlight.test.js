import { HIGHLIGHT_CLASS, searchHighlight } from "@mail/core/common/message_search_hook";
import {
    SIZES,
    click,
    contains,
    defineMailModels,
    insertText,
    openDiscuss,
    openFormView,
    patchUiSize,
    start,
    startServer,
    triggerHotkey,
} from "@mail/../tests/mail_test_helpers";

import { describe, expect, test } from "@sigil/hoot";
import { markup } from "@sigil/owl";

import { serverState } from "@web/../tests/web_test_helpers";

describe.current.tags("desktop");
defineMailModels();

test("Search highlight", async () => {
    const testCases = [
        {
            input: markup`test sigil`,
            output: `test <span class="${HIGHLIGHT_CLASS}">sigil</span>`,
            searchTerm: "sigil",
        },
        {
            input: markup`<a href="https://www.iantirta.com">https://www.iantirta.com</a>`,
            output: `<a href="https://www.iantirta.com">https://www.<span class="${HIGHLIGHT_CLASS}">sigil</span>.com</a>`,
            searchTerm: "sigil",
        },
        {
            input: '<a href="https://www.iantirta.com">https://www.iantirta.com</a>',
            output: `&lt;a href="https://www.<span class="${HIGHLIGHT_CLASS}">sigil</span>.com"&gt;https://www.<span class="${HIGHLIGHT_CLASS}">sigil</span>.com&lt;/a&gt;`,
            searchTerm: "sigil",
        },
        {
            input: markup`<a href="https://www.iantirta.com">Sigil</a>`,
            output: `<a href="https://www.iantirta.com"><span class="${HIGHLIGHT_CLASS}">Sigil</span></a>`,
            searchTerm: "sigil",
        },
        {
            input: markup`<a href="https://www.iantirta.com">Sigil</a> Sigil is a free software`,
            output: `<a href="https://www.iantirta.com"><span class="${HIGHLIGHT_CLASS}">Sigil</span></a> <span class="${HIGHLIGHT_CLASS}">Sigil</span> is a free software`,
            searchTerm: "sigil",
        },
        {
            input: markup`sigil is a free software`,
            output: `<span class="${HIGHLIGHT_CLASS}">sigil</span> is a free software`,
            searchTerm: "sigil",
        },
        {
            input: markup`software SIGIL is a free`,
            output: `software <span class="${HIGHLIGHT_CLASS}">SIGIL</span> is a free`,
            searchTerm: "sigil",
        },
        {
            input: markup`<ul>
                <li>Sigil</li>
                <li><a href="https://iantirta.com">Sigil ERP</a> Best ERP</li>
            </ul>`,
            output: `<ul>
                <li><span class="${HIGHLIGHT_CLASS}">Sigil</span></li>
                <li><a href="https://iantirta.com"><span class="${HIGHLIGHT_CLASS}">Sigil</span> ERP</a> Best ERP</li>
            </ul>`,
            searchTerm: "sigil",
        },
        {
            input: markup`test <strong>Sigil</strong> test`,
            output: `<span class="${HIGHLIGHT_CLASS}">test</span> <strong><span class="${HIGHLIGHT_CLASS}">Sigil</span></strong> <span class="${HIGHLIGHT_CLASS}">test</span>`,
            searchTerm: "sigil test",
        },
        {
            input: markup`test <br> test`,
            output: `<span class="${HIGHLIGHT_CLASS}">test</span> <br> <span class="${HIGHLIGHT_CLASS}">test</span>`,
            searchTerm: "sigil test",
        },
        {
            input: markup`<strong>test</strong> test`,
            output: `<strong><span class="${HIGHLIGHT_CLASS}">test</span></strong> <span class="${HIGHLIGHT_CLASS}">test</span>`,
            searchTerm: "test",
        },
        {
            input: markup`<strong>a</strong> test`,
            output: `<strong><span class="${HIGHLIGHT_CLASS}">a</span></strong> <span class="${HIGHLIGHT_CLASS}">test</span>`,
            searchTerm: "a test",
        },
        {
            input: markup`&amp;amp;`,
            output: `<span class="${HIGHLIGHT_CLASS}">&amp;amp;</span>`,
            searchTerm: "&amp;",
        },
        {
            input: markup`&amp;amp;`,
            output: `<span class="${HIGHLIGHT_CLASS}">&amp;</span>amp;`,
            searchTerm: "&",
        },
        {
            input: markup`<strong>test</strong> hello`,
            output: `<strong><span class="${HIGHLIGHT_CLASS}">test</span></strong> <span class="${HIGHLIGHT_CLASS}">hello</span>`,
            searchTerm: "test hello",
        },
        {
            input: markup`<p>&lt;strong&gt;test&lt;/strong&gt; hello</p>`,
            output: `<p>&lt;strong&gt;<span class="${HIGHLIGHT_CLASS}">test</span>&lt;/strong&gt; <span class="${HIGHLIGHT_CLASS}">hello</span></p>`,
            searchTerm: "test hello",
        },
        {
            input: markup`test sigil`,
            output: `t<span class="${HIGHLIGHT_CLASS}">e</span>st o<span class="${HIGHLIGHT_CLASS}">d</span>oo`,
            searchTerm: "e               d",
        },
    ];
    for (const { input, output, searchTerm } of testCases) {
        expect(searchHighlight(searchTerm, input).toString()).toBe(output);
    }
});

test("Display highlighted search in chatter", async () => {
    patchUiSize({ size: SIZES.XXL });
    const pyEnv = await startServer();
    const partnerId = pyEnv["res.partner"].create({ name: "John Doe" });
    pyEnv["mail.message"].create({
        body: "not empty",
        model: "res.partner",
        res_id: partnerId,
    });
    await start();
    await openFormView("res.partner", partnerId);
    await click("[title='Search Messages']");
    await insertText(".o_searchview_input", "empty");
    triggerHotkey("Enter");
    await contains(`.o-mail-SearchMessageResult .o-mail-Message span.${HIGHLIGHT_CLASS}`);
});

test("Display multiple highlighted search in chatter", async () => {
    patchUiSize({ size: SIZES.XXL });
    const pyEnv = await startServer();
    const partnerId = pyEnv["res.partner"].create({ name: "John Doe" });
    pyEnv["mail.message"].create({
        body: "not test empty",
        model: "res.partner",
        res_id: partnerId,
    });
    await start();
    await openFormView("res.partner", partnerId);
    await click("[title='Search Messages']");
    await insertText(".o_searchview_input", "not empty");
    triggerHotkey("Enter");
    await contains(`.o-mail-SearchMessageResult .o-mail-Message span.${HIGHLIGHT_CLASS}`, {
        count: 2,
    });
});

test("Display highlighted search in Discuss", async () => {
    const pyEnv = await startServer();
    const channelId = pyEnv["discuss.channel"].create({ name: "General" });
    pyEnv["mail.message"].create({
        author_id: serverState.partnerId,
        body: "not empty",
        attachment_ids: [],
        message_type: "comment",
        model: "discuss.channel",
        res_id: channelId,
    });
    await start();
    await openDiscuss(channelId);
    await contains(".o-mail-Message");
    await click("button[title='Search Messages']");
    await insertText(".o_searchview_input", "empty");
    triggerHotkey("Enter");
    await contains(`.o-mail-SearchMessagesPanel .o-mail-Message span.${HIGHLIGHT_CLASS}`);
});

test("Display multiple highlighted search in Discuss", async () => {
    const pyEnv = await startServer();
    const channelId = pyEnv["discuss.channel"].create({ name: "General" });
    pyEnv["mail.message"].create({
        author_id: serverState.partnerId,
        body: "not prout empty",
        attachment_ids: [],
        message_type: "comment",
        model: "discuss.channel",
        res_id: channelId,
    });
    await start();
    await openDiscuss(channelId);
    await contains(".o-mail-Message");
    await click("button[title='Search Messages']");
    await insertText(".o_searchview_input", "not empty");
    triggerHotkey("Enter");
    await contains(`.o-mail-SearchMessagesPanel .o-mail-Message span.${HIGHLIGHT_CLASS}`, {
        count: 2,
    });
});

test("Display highlighted with escaped character must ignore them", async () => {
    patchUiSize({ size: SIZES.XXL });
    const pyEnv = await startServer();
    const partnerId = pyEnv["res.partner"].create({ name: "John Doe" });
    pyEnv["mail.message"].create({
        body: "<p>&lt;strong&gt;test&lt;/strong&gt; hello</p>",
        model: "res.partner",
        res_id: partnerId,
    });
    await start();
    await openFormView("res.partner", partnerId);
    await click("[title='Search Messages']");
    await insertText(".o_searchview_input", "test hello");
    triggerHotkey("Enter");
    await contains(`.o-mail-SearchMessageResult .o-mail-Message span.${HIGHLIGHT_CLASS}`, {
        count: 2,
    });
    await contains(`.o-mail-Message-body`, { text: "<strong>test</strong> hello" });
});
