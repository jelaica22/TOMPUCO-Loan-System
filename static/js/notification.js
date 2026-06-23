function playNotificationSound() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const frequencies = [800, 1000];
        const duration = 0.15;
        frequencies.forEach((freq, index) => {
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();
            oscillator.type = 'sine';
            oscillator.frequency.value = freq;
            gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + duration);
            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            oscillator.start(audioCtx.currentTime + (index * 0.1));
            oscillator.stop(audioCtx.currentTime + (index * 0.1) + duration);
        });
    } catch (e) { console.log('Audio not supported'); }
}

let lastNotificationCount = 0;

function checkForNewNotifications() {
    fetch('/api/notifications/')
        .then(response => response.json())
        .then(data => {
            const unreadCount = data.unread_count || 0;
            const badge = document.getElementById('notificationBadge');
            if (unreadCount > 0) {
                const count = unreadCount > 99 ? '99+' : unreadCount;
                if (badge) {
                    badge.textContent = count;
                    badge.style.display = 'flex';
                }
                if (unreadCount > lastNotificationCount) {
                    playNotificationSound();
                    if ('Notification' in window && Notification.permission === 'granted') {
                        const notif = data.notifications ? data.notifications[0] : null;
                        if (notif) {
                            new Notification('TOMPuCO Notification', {
                                body: notif.title + ': ' + notif.message.substring(0, 60),
                                icon: '/static/images/logo.png'
                            });
                        }
                    }
                }
            } else {
                if (badge) badge.style.display = 'none';
            }
            lastNotificationCount = unreadCount;
        })
        .catch(error => console.error('Error:', error));
}

if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

setInterval(checkForNewNotifications, 15000);

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(checkForNewNotifications, 2000);
});

console.log('Notification system loaded with sound!');
