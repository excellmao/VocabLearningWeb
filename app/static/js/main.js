document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.flip-card');

    cards.forEach(card => {
        card.addEventListener('click', function() {
            this.classList.toggle('flipped');
        });

        card.addEventListener('keydown', function(e) {
            if (e.code === 'Space') {
                e.preventDefault(); // Prevent page from scrolling down
                this.classList.toggle('flipped');
            }
        });
    });
});

function playAudio(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    window.speechSynthesis.speak(utterance);
}