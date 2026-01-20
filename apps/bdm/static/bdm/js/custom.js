// Custom JavaScript for LMS Admin

// Mobile sidebar toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('active');
}

// Close sidebar on mobile when clicking outside
document.addEventListener('click', function(event) {
    const sidebar = document.querySelector('.sidebar');
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    
    if (sidebar && sidebar.classList.contains('active') && 
        !sidebar.contains(event.target) && 
        event.target !== mobileMenuBtn && 
        !mobileMenuBtn.contains(event.target)) {
        sidebar.classList.remove('active');
    }
});

// Toggle dropdown menus
function toggleUserDropdown() {
    const dropdown = document.querySelector('.user-dropdown-menu');
    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

function toggleNotificationDropdown() {
    const dropdown = document.querySelector('.notification-dropdown-menu');
    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    const userDropdown = document.querySelector('.user-dropdown');
    const notificationDropdown = document.querySelector('.notification-dropdown');
    const userMenu = document.querySelector('.user-menu');
    const notificationBtn = document.querySelector('.notification-btn');
    
    if (userDropdown && !userDropdown.contains(event.target) && !userMenu.contains(event.target)) {
        const dropdownMenu = userDropdown.querySelector('.user-dropdown-menu');
        if (dropdownMenu) dropdownMenu.style.display = 'none';
    }
    
    if (notificationDropdown && !notificationDropdown.contains(event.target) && !notificationBtn.contains(event.target)) {
        const dropdownMenu = notificationDropdown.querySelector('.notification-dropdown-menu');
        if (dropdownMenu) dropdownMenu.style.display = 'none';
    }
});

// Set active sidebar link based on current URL
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    
    sidebarLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

// Greeting based on time of day
function updateGreeting() {
    const hour = new Date().getHours();
    const greeting = document.getElementById('greeting');
    
    if (greeting) {
        if (hour < 12) {
            greeting.textContent = 'Good morning, ' + greeting.textContent.split(', ')[1];
        } else if (hour < 18) {
            greeting.textContent = 'Good afternoon, ' + greeting.textContent.split(', ')[1];
        } else {
            greeting.textContent = 'Good evening, ' + greeting.textContent.split(', ')[1];
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    updateGreeting();
    
    // Auto-hide notifications after 5 seconds
    setTimeout(() => {
        const notifications = document.querySelectorAll('.notification-item');
        notifications.forEach(notification => {
            notification.style.opacity = '0.7';
        });
    }, 5000);
});

// Search functionality
function handleSearch(event) {
    if (event.key === 'Enter') {
        const searchInput = event.target;
        const query = searchInput.value.trim();
        
        if (query) {
            // Implement search functionality here
            console.log('Searching for:', query);
            // You can redirect to search results page or make an API call
        }
    }
}