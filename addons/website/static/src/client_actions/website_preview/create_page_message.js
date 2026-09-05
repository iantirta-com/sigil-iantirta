import { Component } from "@sigil/owl";

export class CreatePageMessage extends Component {
    static template = "website.CreatePageMessage";
    static props = {
        createPage: { type: Function },
    };
}
