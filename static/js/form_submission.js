document.addEventListener('DOMContentLoaded', function() {
    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    document.querySelector('input[type="date"]')?.setAttribute('min', today);
    
    // Faculty selection functionality
    document.querySelectorAll('.faculty-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const card = this.closest('.faculty-card');
            if (this.checked) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
        });
    });

    // Time duration calculation for OD form
    if (document.getElementById('start_time') && document.getElementById('end_time')) {
        const startTime = document.getElementById('start_time');
        const endTime = document.getElementById('end_time');
        const durationDisplay = document.getElementById('duration');
        const durationHidden = document.getElementById('duration_hidden');
        
        function calculateDuration() {
            if (startTime.value && endTime.value) {
                const startParts = startTime.value.split(':');
                const endParts = endTime.value.split(':');
                
                const startHours = parseInt(startParts[0]);
                const startMinutes = parseInt(startParts[1]);
                const endHours = parseInt(endParts[0]);
                const endMinutes = parseInt(endParts[1]);
                
                let totalMinutes = (endHours * 60 + endMinutes) - (startHours * 60 + startMinutes);
                
                if (totalMinutes < 0) {
                    totalMinutes += 24 * 60; // Handle overnight (though shouldn't happen with our time range)
                }
                
                const hours = Math.floor(totalMinutes / 60);
                const minutes = totalMinutes % 60;
                
                durationDisplay.value = `${hours} hours ${minutes} minutes`;
                durationHidden.value = `${hours}.${Math.round(minutes/60*100)}`; // Store as decimal for calculations
            }
        }
        
        startTime.addEventListener('change', calculateDuration);
        endTime.addEventListener('change', calculateDuration);
    }
    
    // Days calculation for Leave form
    if (document.getElementById('start_date') && document.getElementById('end_date')) {
        const startDate = document.getElementById('start_date');
        const endDate = document.getElementById('end_date');
        const days = document.getElementById('days');
        
        function calculateDays() {
            if (startDate.value && endDate.value) {
                const start = new Date(startDate.value);
                const end = new Date(endDate.value);
                const diff = Math.floor((end - start) / (1000 * 60 * 60 * 24));
                days.value = diff > 0 ? diff + 1 : 1;
            }
        }
        
        startDate.addEventListener('change', calculateDays);
        endDate.addEventListener('change', calculateDays);
    }
});
