/** @sigil-module **/

import { animationFrame, before, expect, test } from "@sigil/hoot";
import { Component, xml } from "@sigil/owl";
import { BarcodeScanner } from "@barcodes/components/barcode_scanner";
import { contains, mountWithCleanup } from "@web/../tests/web_test_helpers";
import { loadJS } from "@web/core/assets";

before(() => loadJS("/web/static/lib/zxing-library/zxing-library.js"));

test.tags("desktop");
test("Display notification for media device permission on barcode scanning", async () => {
    navigator.mediaDevices.getUserMedia = function () {
        return Promise.reject(new DOMException("", "NotAllowedError"));
    };

    class BarcodeScan extends Component {
        static template = xml`
            <div>
                <BarcodeScanner onBarcodeScanned="(ev) => this.onBarcodeScanned(ev)"/>
            </div>
        `;
        static components = { BarcodeScanner };
        static props = ["*"];
    }

    await mountWithCleanup(BarcodeScan);
    await contains("a.o_mobile_barcode").click();
    // first rendering: dialog with BarcodeVideoScanner which throws in onMounted
    // => second rendering: displays "Unable to access camera" in the dialog
    await animationFrame();
    expect(".modal-body").toHaveText(
        "Unable to access camera\nCould not start scanning. Sigil needs your authorization first."
    );
});
