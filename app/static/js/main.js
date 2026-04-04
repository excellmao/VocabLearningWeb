document.addEventListener('DOMContentLoaded', () => {

    function playAudio(text) {
        // Stop any currently playing audio so they don't overlap
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US'; // You can change this if you are learning a different language!
        window.speechSynthesis.speak(utterance);
    }

    // Attach listeners to all flashcards
    document.querySelectorAll('.flip-card').forEach(card => {

        // Handle Mouse Click
        card.addEventListener('click', function() {
            // 1. Flip the card
            this.classList.toggle('flipped');

            // 2. Grab the word and play the audio
            const term = this.getAttribute('data-term');
            if (term) {
                playAudio(term);
            }
        });

        // Keep Keyboard Accessibility (Spacebar / Enter)
        card.addEventListener('keydown', function(e) {
            if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault(); // Stop the spacebar from scrolling the page down
                this.click(); // Trigger the click event we just wrote above
            }
        });
    });
});