class CalendarExtension {
    constructor() {
        this.currentDate = new Date();
        this.selectedDate = null;
        this.apiBaseUrl = 'http://localhost:5000';
        this.init();
    }

    init() {
        this.renderCalendar();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('prevMonth').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this.renderCalendar();
        });

        document.getElementById('nextMonth').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this.renderCalendar();
        });
    }

    renderCalendar() {
        const monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        
        // Update month header
        document.getElementById('currentMonth').textContent = 
            `${monthNames[this.currentDate.getMonth()]} ${this.currentDate.getFullYear()}`;
        
        const grid = document.getElementById('calendarGrid');
        grid.innerHTML = '';
        
        // Add day headers
        dayNames.forEach(day => {
            const dayHeader = document.createElement('div');
            dayHeader.className = 'calendar-day day-header';
            dayHeader.textContent = day;
            grid.appendChild(dayHeader);
        });
        
        // Get first day of month and number of days
        const firstDay = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
        const lastDay = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 0);
        const daysInMonth = lastDay.getDate();
        const startingDayOfWeek = firstDay.getDay();
        
        // Add empty cells for previous month
        for (let i = 0; i < startingDayOfWeek; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'calendar-day other-month';
            const prevMonthDay = new Date(firstDay);
            prevMonthDay.setDate(prevMonthDay.getDate() - (startingDayOfWeek - i));
            emptyDay.textContent = prevMonthDay.getDate();
            grid.appendChild(emptyDay);
        }
        
        // Add days of current month
        for (let day = 1; day <= daysInMonth; day++) {
            const dayElement = document.createElement('div');
            dayElement.className = 'calendar-day';
            dayElement.textContent = day;
            
            const currentDayDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), day);
            
            // Add click event
            dayElement.addEventListener('click', (event) => {
                this.selectDate(currentDayDate, event);
            });
            
            grid.appendChild(dayElement);
        }
        
        // Add remaining cells for next month
        const totalCells = grid.children.length;
        const remainingCells = 42 - totalCells; // 6 rows × 7 days
        for (let i = 1; i <= remainingCells; i++) {
            const nextMonthDay = document.createElement('div');
            nextMonthDay.className = 'calendar-day other-month';
            nextMonthDay.textContent = i;
            grid.appendChild(nextMonthDay);
        }
    }

    selectDate(date, event) {
        // Remove previous selection
        document.querySelectorAll('.calendar-day.selected').forEach(day => {
            day.classList.remove('selected');
        });
        
        // Add selection to clicked day
        event.target.classList.add('selected');
        
        this.selectedDate = date;
        this.updateSelectedDateDisplay();
        this.loadMeetingsForDate(date);
    }

    updateSelectedDateDisplay() {
        const dateDisplay = document.getElementById('selectedDate');
        if (this.selectedDate) {
            const options = { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            };
            dateDisplay.innerHTML = `<h3>📅 ${this.selectedDate.toLocaleDateString('en-US', options)}</h3>`;
        }
    }

    async loadMeetingsForDate(date) {
        const loading = document.getElementById('loading');
        const container = document.getElementById('meetingsContainer');
        const status = document.getElementById('status');
        
        // Show loading with rotating company logos
        loading.style.display = 'block';
        loading.innerHTML = '<img src="https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png" alt="LinkedIn" class="loading-logo">';
        container.innerHTML = '';
        status.textContent = '';
        
        // Start logo rotation
        const logos = [
            { src: 'https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png', alt: 'LinkedIn' },
            { src: 'https://www.google.com/favicon.ico', alt: 'Google' },
            { src: 'https://upload.wikimedia.org/wikipedia/en/8/80/Wikipedia-logo-v2.svg', alt: 'Wikipedia' },
            { src: 'https://tavily.com/favicon.ico', alt: 'Tavily' }
        ];
        let logoIndex = 0;
        const logoInterval = setInterval(() => {
            logoIndex = (logoIndex + 1) % logos.length;
            loading.innerHTML = `<img src="${logos[logoIndex].src}" alt="${logos[logoIndex].alt}" class="loading-logo">`;
        }, 500);
        
        // Store interval ID for cleanup
        loading.logoInterval = logoInterval;
        
        try {
            const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD format
            
            const response = await fetch(`${this.apiBaseUrl}/meetings/${dateStr}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Hide loading and stop logo rotation
            loading.style.display = 'none';
            if (loading.logoInterval) {
                clearInterval(loading.logoInterval);
                loading.logoInterval = null;
            }
            
            if (data.meetings && data.meetings.length > 0) {
                this.displayMeetings(data.meetings);
                this.showStatus('success', `Found ${data.meetings.length} meeting(s)`);
            } else {
                this.displayNoMeetings();
                this.showStatus('success', 'No meetings found for this date');
            }
            
        } catch (error) {
            console.error('Error loading meetings:', error);
            loading.style.display = 'none';
            if (loading.logoInterval) {
                clearInterval(loading.logoInterval);
                loading.logoInterval = null;
            }
            this.displayError(error.message);
            this.showStatus('error', 'Failed to load meetings. Make sure the backend server is running.');
        }
    }

    displayMeetings(meetings) {
        const container = document.getElementById('meetingsContainer');
        container.innerHTML = '';
        
        meetings.forEach(meeting => {
            const meetingElement = document.createElement('div');
            meetingElement.className = 'meeting-item';
            
            const title = document.createElement('div');
            title.className = 'meeting-title';
            title.textContent = meeting.title || meeting.meeting_title || 'Untitled Meeting';
            
            const people = document.createElement('div');
            people.className = 'meeting-people';
            const attendees = meeting.people || meeting.person_names || [];
            people.textContent = attendees && attendees.length > 0 
                ? `👥 ${attendees.join(', ')}`
                : '👥 No attendees listed';
            
            const time = document.createElement('div');
            time.className = 'meeting-time';
            const startTime = meeting.start_time;
            if (startTime) {
                const timeDate = new Date(startTime);
                time.textContent = `🕐 ${timeDate.toLocaleTimeString('en-US', { 
                    hour: 'numeric', 
                    minute: '2-digit',
                    hour12: true 
                })}`;
            }
            
            // Add research button if research data is available
            if (meeting.research_summary || meeting.preparation_questions) {
                const researchBtn = document.createElement('button');
                researchBtn.className = 'research-btn';
                researchBtn.textContent = '🔍 Research';
                researchBtn.addEventListener('click', () => {
                    this.showMeetingResearch(meeting);
                });
                meetingElement.appendChild(researchBtn);
            }
            
            meetingElement.appendChild(title);
            meetingElement.appendChild(people);
            meetingElement.appendChild(time);
            
            container.appendChild(meetingElement);
        });
    }

    displayNoMeetings() {
        const container = document.getElementById('meetingsContainer');
        container.innerHTML = '<div class="no-meetings">📭 No meetings scheduled for this date</div>';
    }

    displayError(message) {
        const container = document.getElementById('meetingsContainer');
        container.innerHTML = `<div class="no-meetings">❌ Error: ${message}</div>`;
    }

    showStatus(type, message) {
        const status = document.getElementById('status');
        status.className = `status ${type}`;
        status.textContent = message;
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            status.textContent = '';
            status.className = 'status';
        }, 3000);
    }

    showMeetingResearch(meeting) {
        const researchContainer = document.getElementById('researchContainer');
        const researchContent = document.getElementById('researchContent');
        
        // Build research content
        let content = `
            <div class="meeting-research">
                <h4>📅 ${meeting.title || meeting.meeting_title}</h4>
                <div class="meeting-meta">
                    ${meeting.start_time ? `<p><strong>Time:</strong> ${new Date(meeting.start_time).toLocaleString()}</p>` : ''}
                    ${meeting.location ? `<p><strong>Location:</strong> ${meeting.location}</p>` : ''}
                </div>
        `;
        
        // Add attendees with research
        if (meeting.attendees && meeting.attendees.length > 0) {
            content += '<div class="attendees-section"><h5>👥 Attendees & Research</h5>';
            meeting.attendees.forEach(attendee => {
                content += `
                    <div class="attendee-card">
                        <h6>${attendee.name}</h6>
                        ${attendee.email ? `<p><strong>Email:</strong> ${attendee.email}</p>` : ''}
                        ${attendee.company ? `<p><strong>Company:</strong> ${attendee.company}</p>` : ''}
                        ${attendee.title ? `<p><strong>Title:</strong> ${attendee.title}</p>` : ''}
                        ${attendee.research_summary ? `<div class="research-summary"><strong>Research:</strong><br>${attendee.research_summary.substring(0, 200)}...</div>` : ''}
                    </div>
                `;
            });
            content += '</div>';
        }
        
        // Add meeting analysis
        if (meeting.research_summary) {
            content += `
                <div class="meeting-analysis">
                    <h5>📊 Meeting Analysis</h5>
                    <div class="analysis-content">${meeting.research_summary.substring(0, 500)}...</div>
                </div>
            `;
        }
        
        // Add preparation questions
        if (meeting.preparation_questions) {
            content += `
                <div class="preparation-questions">
                    <h5>❓ Preparation Questions</h5>
                    <div class="questions-content">${meeting.preparation_questions.substring(0, 500)}...</div>
                </div>
            `;
        }
        
        content += '</div>';
        
        researchContent.innerHTML = content;
        researchContainer.style.display = 'block';
        
        // Add close button functionality
        document.getElementById('closeResearch').addEventListener('click', () => {
            researchContainer.style.display = 'none';
        });
    }
}

// Initialize the extension when popup loads
document.addEventListener('DOMContentLoaded', () => {
    new CalendarExtension();
});
