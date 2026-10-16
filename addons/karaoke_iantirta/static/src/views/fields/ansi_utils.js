const COLORS = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'inherit', 'transparent'];
const styleMap = {
    '0': '',                    // Reset
    '1': 'font-weight: bold;',
};

const ansiRegex = /\u001b\[([0-9;]+)m/g;

export function ansiToStyleColor(text) {
    let openSpan = false;

    return text.replace(ansiRegex, (match, codeString) => {
        const codes = codeString.split(';');
        let styles = [];

        if (codes.includes('0')) {
            const closingTag = openSpan ? '</span>' : '';
            openSpan = false;
            return closingTag;
        }

        codes.forEach(code => {
            const intCode = parseInt(code, 10);

            if (intCode >= 30 && intCode < 40) {
                const colorName = COLORS[intCode - 30];
                styles.push(`color: ${colorName};`);
            }
            else if (intCode >= 40 && intCode < 50) {
                const colorName = COLORS[intCode - 40];
                styles.push(`background-color: ${colorName};`);
            }
            else if (styleMap[code]) {
                styles.push(styleMap[code]);
            }
        });

        if (styles.length > 0) {
            const prefix = openSpan ? '</span>' : '';
            openSpan = true;
            return `${prefix}<span style="${styles.join(' ')}">`;
        }

        return '';
    }) + (openSpan ? '</span>' : '');
}

export function stripAnsi(text) {
    if (!text) return "";
    return text.toString().replace(ansiRegex, '');
}