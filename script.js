// Demo Scenarios
const scenarios = {
    health: [
        { role: 'user', text: 'I need to file a health insurance claim' },
        { role: 'ai', text: "I'll help you file a health insurance claim. Could you please tell me:\n\n1. Your full name\n2. Policy number (if you have it)\n3. Date of hospital visit\n4. Brief description of treatment" },
        { role: 'user', text: 'John Doe, policy HL-12345, last week for appendectomy' },
        { role: 'ai', text: "Thank you, John. I've created claim BJK-A1B2C3D4 for your appendectomy.\n\n✓ Claim submitted successfully\n✓ Policy verified\n\nNext steps: Please upload your hospital bill and discharge summary. You can do this through the app or I can help you here." },
        { role: 'user', text: 'What documents do I need?' },
        { role: 'ai', text: "For health insurance claims, you'll need:\n\n1. Hospital bill and receipts\n2. Discharge summary\n3. Policy number (you've provided this)\n4. Medical reports and prescriptions\n\nI've found this from our FAQ knowledge base. All documents should be original or certified copies." }
    ],
    motor: [
        { role: 'user', text: 'I was in a car accident yesterday' },
        { role: 'ai', text: "I'm sorry to hear that. I'll help you file a motor insurance claim. Please provide:\n\n1. Your name and policy number\n2. Date and time of accident\n3. Location of accident\n4. Description of damage\n5. Was anyone else involved?" },
        { role: 'user', text: 'Jane Smith, MOT-67890, yesterday at 3pm on Main Street. Front bumper damaged. Other driver was at fault.' },
        { role: 'ai', text: "I've created claim BJK-E5F6G7H8 for your motor incident.\n\n✓ Claim submitted\n✓ Third-party incident noted\n\nImportant: Since another driver was at fault, please:\n1. File a police report if not done already\n2. Take photos of both vehicles\n3. Exchange insurance information\n\nWould you like me to guide you through the next steps?" }
    ],
    faq: [
        { role: 'user', text: 'What is covered under travel insurance?' },
        { role: 'ai', text: "Based on BJAK's travel insurance policy, coverage includes:\n\n• Medical emergencies abroad\n• Trip cancellation/interruption\n• Lost or delayed baggage\n• Travel delays\n• Personal liability\n\nNote: Pre-existing conditions and high-risk activities may have exclusions. Would you like details on any specific coverage?" },
        { role: 'user', text: 'How do I renew my policy?' },
        { role: 'ai', text: "You can renew your policy through:\n\n1. **BJAK App**: Go to Policies > Select Policy > Renew\n2. **Website**: Login and click Renew on your dashboard\n3. **Call us**: 1800-XXX-XXXX\n\nRenew before your due date to avoid policy lapse. During the 30-day grace period, your coverage continues but renewal after that may require fresh underwriting." }
    ],
    status: [
        { role: 'user', text: 'What is the status of my claim?' },
        { role: 'ai', text: "I can help you track your claim. Please provide your claim ID (format: BJK-XXXXXXXX)." },
        { role: 'user', text: 'BJK-A1B2C3D4' },
        { role: 'ai', text: "Here's the status of claim **BJK-A1B2C3D4**:\n\n📋 **Status**: Under Review\n📅 **Submitted**: March 15, 2024\n💰 **Amount**: $4,500.00\n\n**Timeline:**\n✓ Submitted - Mar 15, 10:30 AM\n✓ Documents Received - Mar 15, 11:45 AM\n⏳ Under Review - Mar 16, 2:00 PM\n○ Approval Pending\n\nOur team is reviewing your documents. You should receive an update within 2-3 business days." }
    ]
};

// Demo Chat Functionality
class DemoChat {
    constructor() {
        this.chat = document.getElementById('demoChat');
        this.input = document.getElementById('demoInput');
        this.sendBtn = document.getElementById('demoSend');
        this.scenarioBtns = document.querySelectorAll('.scenario-btn');
        this.currentScenario = 'health';
        this.messageIndex = 0;
        
        this.init();
    }
    
    init() {
        // Scenario buttons
        this.scenarioBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.scenarioBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentScenario = btn.dataset.scenario;
                this.resetChat();
                this.playDemo();
            });
        });
        
        // Send button (for manual input - simulated)
        this.sendBtn.addEventListener('click', () => this.handleManualInput());
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleManualInput();
        });
        
        // Start demo after delay
        setTimeout(() => this.playDemo(), 1000);
    }
    
    resetChat() {
        this.messageIndex = 0;
        this.chat.innerHTML = `
            <div class="chat-message ai">
                <div class="message-avatar">AI</div>
                <div class="message-content">
                    Hello! I'm your AI Claims Assistant. How can I help you today?
                </div>
            </div>
        `;
    }
    
    async playDemo() {
        const scenario = scenarios[this.currentScenario];
        if (!scenario) return;
        
        for (let i = 0; i < scenario.length; i++) {
            await this.delay(1500);
            this.addMessage(scenario[i].role, scenario[i].text);
        }
        
        // Enable manual input after demo
        this.input.disabled = false;
        this.sendBtn.disabled = false;
        this.input.placeholder = 'Type your message...';
    }
    
    addMessage(role, text) {
        const isUser = role === 'user';
        const messageHTML = `
            <div class="chat-message ${isUser ? 'user' : 'ai'}">
                <div class="message-avatar">${isUser ? 'You' : 'AI'}</div>
                <div class="message-content">${this.formatText(text)}</div>
            </div>
        `;
        
        this.chat.insertAdjacentHTML('beforeend', messageHTML);
        this.chat.scrollTop = this.chat.scrollHeight;
    }
    
    formatText(text) {
        // Simple markdown-like formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }
    
    handleManualInput() {
        const text = this.input.value.trim();
        if (!text) return;
        
        this.addMessage('user', text);
        this.input.value = '';
        
        // Simulate AI response
        setTimeout(() => {
            const response = this.generateResponse(text);
            this.addMessage('ai', response);
        }, 1000);
    }
    
    generateResponse(input) {
        const lower = input.toLowerCase();
        
        if (lower.includes('claim') && lower.includes('status')) {
            return "I can help you track your claim. Please provide your claim ID in the format BJK-XXXXXXXX.";
        }
        if (lower.includes('file') || lower.includes('new claim')) {
            return "I'll help you file a new claim. What type of insurance is this for? (health, motor, life, or travel)";
        }
        if (lower.includes('document') || lower.includes('upload')) {
            return "You can upload documents through:\n1. The BJAK app (Camera or File upload)\n2. This chat (drag and drop)\n3. Email to claims@bjak.com\n\nAccepted formats: PDF, JPG, PNG";
        }
        if (lower.includes('human') || lower.includes('agent') || lower.includes('manager')) {
            return "I understand you'd like to speak with a human agent. I'm escalating your request now. A claims specialist will contact you within 24 hours. Your reference number is BJK-ESC-" + Math.random().toString(36).substr(2, 6).toUpperCase();
        }
        
        return "Thank you for your message. I'm here to help with insurance claims. You can:\n\n• File a new claim\n• Check claim status\n• Ask FAQ questions\n• Upload documents\n\nWhat would you like to do?";
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Smooth scroll for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar scroll effect
const navbar = document.querySelector('.navbar');
let lastScroll = 0;

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        navbar.style.boxShadow = 'var(--shadow-md)';
    } else {
        navbar.style.boxShadow = 'none';
    }
    
    lastScroll = currentScroll;
});

// Mobile menu toggle
const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
const navLinks = document.querySelector('.nav-links');
const navActions = document.querySelector('.nav-actions');

if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => {
        navLinks.classList.toggle('mobile-open');
        navActions.classList.toggle('mobile-open');
    });
}

// Initialize demo chat
document.addEventListener('DOMContentLoaded', () => {
    new DemoChat();
});

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
        }
    });
}, observerOptions);

// Observe elements for animation
document.querySelectorAll('.feature-card, .step, .tech-card').forEach(el => {
    observer.observe(el);
});

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    .feature-card, .step, .tech-card {
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 0.6s ease, transform 0.6s ease;
    }
    
    .feature-card.animate-in, .step.animate-in, .tech-card.animate-in {
        opacity: 1;
        transform: translateY(0);
    }
    
    .nav-links.mobile-open, .nav-actions.mobile-open {
        display: flex;
        position: absolute;
        top: 72px;
        left: 0;
        right: 0;
        flex-direction: column;
        background: white;
        padding: 20px;
        border-bottom: 1px solid var(--color-gray-200);
        box-shadow: var(--shadow-lg);
    }
    
    .nav-actions.mobile-open {
        top: auto;
        padding-top: 0;
    }
    
    .nav-links.mobile-open .nav-link {
        padding: 12px 0;
    }
`;
document.head.appendChild(style);
