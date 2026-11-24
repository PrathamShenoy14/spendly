// Landing page: "See how it works" video modal (vanilla JS, no dependencies)

(function () {
    var openBtn = document.getElementById('open-video-modal');
    var closeBtn = document.getElementById('close-video-modal');
    var modal = document.getElementById('video-modal');
    var iframe = document.getElementById('video-modal-iframe');

    if (!openBtn || !modal || !iframe) return;

    function openModal(e) {
        e.preventDefault();
        // Load the video only when opened so it starts playing on demand.
        iframe.src = iframe.dataset.src;
        modal.hidden = false;
        document.body.classList.add('modal-open');
        closeBtn.focus();
    }

    function closeModal() {
        if (modal.hidden) return;
        modal.hidden = true;
        document.body.classList.remove('modal-open');
        // Clearing the src unloads the player, which stops playback.
        iframe.src = '';
        openBtn.focus();
    }

    openBtn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);

    // Click on the dark backdrop (outside the content box) closes the modal.
    modal.addEventListener('click', function (e) {
        if (e.target === modal) closeModal();
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeModal();
    });
})();
