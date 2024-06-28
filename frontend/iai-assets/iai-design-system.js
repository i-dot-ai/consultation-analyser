// @ts-check


/**
 * Wrap around a <button> element to make it toggleable
 */
class ToggleButton extends HTMLElement {
    connectedCallback() {
        const button = this.querySelector('button');
        button?.addEventListener('click', () => {
            const expanded = button.getAttribute('aria-expanded') == 'true';
            button.setAttribute('aria-expanded', expanded ? 'false' : 'true');
        });
    }
}
customElements.define('toggle-button', ToggleButton);