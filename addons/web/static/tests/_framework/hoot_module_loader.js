// @sigil-module ignore
// ! WARNING: this module must be loaded after `module_loader` but cannot have dependencies !

(function (sigil) {
    "use strict";

    if (sigil.define.name.endsWith("(hoot)")) {
        return;
    }

    const name = `${sigil.define.name} (hoot)`;
    sigil.define = {
        [name](name, dependencies, factory) {
            return sigil.loader.define(name, dependencies, factory, !name.endsWith(".hoot"));
        },
    }[name];
})(globalThis.sigil);
