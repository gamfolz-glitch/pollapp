/**
 * JavaScript для таймера опроса
 */
function initPollTimer(totalSeconds) {
  if (!totalSeconds || totalSeconds <= 0) return;
  
  const timerElement = document.getElementById('poll-timer');
  const containerElement = document.getElementById('poll-timer-container');
  
  if (!timerElement || !containerElement) return;
  
  function updateTimer() {
    const mins = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
    const secs = String(totalSeconds % 60).padStart(2, '0');
    timerElement.textContent = `${mins}:${secs}`;
    
    if (totalSeconds <= 0) {
      clearInterval(timer);
      document.querySelectorAll('form *').forEach(el => el.disabled = true);
      containerElement.innerHTML = 
        '<div class="text-red-600 font-semibold flex items-center justify-center gap-2"><i class="fas fa-clock"></i> ⏰ Время вышло! Ответы больше не принимаются.</div>';
      
      setTimeout(() => window.location.reload(), 2000);
      return;
    }
    totalSeconds--;
  }
  
  const timer = setInterval(updateTimer, 1000);
  updateTimer();
}

