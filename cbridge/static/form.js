document.addEventListener('DOMContentLoaded', function() {
    const maxWidth = 40; // Maximum width in characters to avoid excessively wide fields

    function calculateDimensions(input, maxLength) {
        const style = window.getComputedStyle(input);
        const fontSize = parseFloat(style.fontSize) || 16; // Default to 16px if not defined
        console.log(fontSize)
        const viewportWidth = window.innerWidth;
        const inputLeft = input.getBoundingClientRect().left;

        // Calculate the max width allowed without overflowing the viewport
        const maxAllowedWidth = viewportWidth - inputLeft - 20; // 20px padding

        // Calculate width in 'rem' units
        const characterWidth = fontSize * 0.8; // Approximate width of a character in px
        const maxWidthInPx = maxLength * characterWidth;
        const widthInRem = maxWidthInPx / fontSize;

        // Calculate height if necessary (in rows)
        const rows = Math.ceil(maxWidthInPx / maxAllowedWidth);
 
        return {
            width: widthInRem + 'rem',
            rows: rows
        };
    }

    function adjustField(input) {
        const maxLength = parseInt(input.getAttribute('maxlength'), 10);
        if (maxLength) {
            const dimensions = calculateDimensions(input, maxLength);

            if (input.tagName === 'INPUT') {
                input.style.width = dimensions.width;
            }

            // Switch to textarea if necessary
            if (maxLength > maxWidth) {
                if (input.tagName === 'INPUT') {
                    const textarea = document.createElement('textarea');
                    textarea.setAttribute('maxlength', maxLength);
                    textarea.setAttribute('name', input.getAttribute('name'));
                    textarea.setAttribute('id', input.getAttribute('id'));
                    textarea.value = input.value;
                    textarea.className = input.className; // Keep existing classes
                    textarea.setAttribute('rows', dimensions.rows);
                    if (input.hasAttribute('required')) {
                        textarea.setAttribute('required', 'required');
                    }

                    input.parentNode.replaceChild(textarea, input);
                } else if (input.tagName === 'TEXTAREA') {
                    input.style.width = dimensions.width;
                    input.setAttribute('rows', dimensions.rows);
                }
            }
        }
    }

    // Adjust fields initially
    document.querySelectorAll('input[maxlength], textarea[maxlength]').forEach(adjustField);

    // Adjust fields on window resize
    window.addEventListener('resize', function() {
        document.querySelectorAll('input[maxlength], textarea[maxlength]').forEach(adjustField);
    });
});
