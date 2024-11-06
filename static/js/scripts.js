window.addEventListener('DOMContentLoaded', () => {
    let scrollPos = 0;
    const mainNav = document.getElementById('mainNav');
    const headerHeight = mainNav.clientHeight;

    window.addEventListener('scroll', () => {
        const currentTop = -document.body.getBoundingClientRect().top;

        if (currentTop < scrollPos) {
            // Scrolling Up
            if (currentTop > 0 && mainNav.classList.contains('is-fixed')) {
                mainNav.classList.add('is-visible');
            } else {
                mainNav.classList.remove('is-visible', 'is-fixed');
            }
        } else {
            // Scrolling Down
            mainNav.classList.remove('is-visible');
            if (currentTop > headerHeight && !mainNav.classList.contains('is-fixed')) {
                mainNav.classList.add('is-fixed');
            }
        }
        scrollPos = currentTop;
    });

    // Set the current year
    document.getElementById("year").textContent = new Date().getFullYear();

    // Reset form if the message has been sent
    const msgSent = {{ msg_sent | tojson }};
    if (msgSent) {
        const form = document.querySelector('form');
        if (form) form.reset();
    }

});
