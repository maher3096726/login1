/**
 * المعهد العالي للعلوم الإدارية ببلقاس
 * main.js - الوظائف العامة للموقع
 */

// ===================== دوال عامة =====================

// إظهار رسالة تنبيه
function showMessage(message, type = 'info') {
    const alertDiv = document.getElementById('global-alert');
    if (alertDiv) {
        alertDiv.className = `alert ${type}`;
        alertDiv.innerHTML = message;
        alertDiv.style.display = 'block';
        
        setTimeout(() => {
            alertDiv.style.display = 'none';
        }, 5000);
    } else {
        // إذا لم يوجد عنصر التنبيه، نستخدم alert العادي
        if (type === 'error') {
            alert('❌ ' + message);
        } else if (type === 'success') {
            alert('✅ ' + message);
        } else {
            alert(message);
        }
    }
}

// إظهار مؤشر التحميل
function showLoading() {
    const loader = document.getElementById('global-loading');
    if (loader) {
        loader.classList.add('active');
    }
}

// إخفاء مؤشر التحميل
function hideLoading() {
    const loader = document.getElementById('global-loading');
    if (loader) {
        loader.classList.remove('active');
    }
}

// التحقق من صحة رقم الهاتف المصري
function validateEgyptianPhone(phone) {
    const phonePattern = /^01[0-9]{9}$/;
    return phonePattern.test(phone);
}

// التحقق من صحة الرقم القومي (14 رقم)
function validateNationalId(nationalId) {
    const idPattern = /^\d{14}$/;
    return idPattern.test(nationalId);
}

// التحقق من صحة رقم الجلوس
function validateSeatNumber(seat) {
    const seatPattern = /^\d{5,7}$/;
    return seatPattern.test(seat);
}

// تنسيق التاريخ العربي
function formatArabicDate(date) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        weekday: 'long'
    };
    return date.toLocaleDateString('ar-EG', options);
}

// نسخ النص إلى الحافظة
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showMessage('تم نسخ النص بنجاح!', 'success');
    }).catch(() => {
        showMessage('فشل نسخ النص', 'error');
    });
}

// ===================== دوال معالجة الصور =====================

// تحويل الصورة إلى Base64
function imageToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// ضغط الصورة قبل الرفع
async function compressImage(file, maxWidth = 1024, maxHeight = 1024, quality = 0.8) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                let width = img.width;
                let height = img.height;
                
                // حساب الأبعاد الجديدة
                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }
                if (height > maxHeight) {
                    width = (width * maxHeight) / height;
                    height = maxHeight;
                }
                
                // رسم الصورة بحجم جديد
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                // تحويل إلى Base64
                const base64 = canvas.toDataURL('image/jpeg', quality);
                resolve(base64);
            };
            img.onerror = reject;
            img.src = e.target.result;
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// ===================== دوال API =====================

// إرسال طلب GET
async function apiGet(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API GET Error:', error);
        throw error;
    }
}

// إرسال طلب POST
async function apiPost(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API POST Error:', error);
        throw error;
    }
}

// ===================== دوال التخزين المحلي =====================

// حفظ بيانات في localStorage
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('LocalStorage save error:', error);
        return false;
    }
}

// استرجاع بيانات من localStorage
function getFromLocalStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('LocalStorage get error:', error);
        return null;
    }
}

// حذف بيانات من localStorage
function removeFromLocalStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('LocalStorage remove error:', error);
        return false;
    }
}

// ===================== دوال واجهة المستخدم =====================

// تبديل وضع الظلام/النهار
function toggleDarkMode() {
    const body = document.body;
    const isDark = body.classList.toggle('dark-mode');
    saveToLocalStorage('darkMode', isDark);
    
    const icon = document.querySelector('#darkModeToggle i');
    if (icon) {
        icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// تهيئة وضع الظلام
function initDarkMode() {
    const isDark = getFromLocalStorage('darkMode');
    if (isDark) {
        document.body.classList.add('dark-mode');
        const icon = document.querySelector('#darkModeToggle i');
        if (icon) icon.className = 'fas fa-sun';
    }
}

// إنشاء عنصر HTML ديناميكياً
function createElement(tag, attributes = {}, children = []) {
    const element = document.createElement(tag);
    
    // إضافة السمات
    Object.keys(attributes).forEach(key => {
        if (key === 'className') {
            element.className = attributes[key];
        } else if (key === 'style' && typeof attributes[key] === 'object') {
            Object.assign(element.style, attributes[key]);
        } else {
            element.setAttribute(key, attributes[key]);
        }
    });
    
    // إضافة الأطفال
    children.forEach(child => {
        if (typeof child === 'string') {
            element.appendChild(document.createTextNode(child));
        } else if (child instanceof HTMLElement) {
            element.appendChild(child);
        }
    });
    
    return element;
}

// ===================== دوال التحقق من صحة النماذج =====================

// التحقق من النموذج
function validateForm(formId, rules) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    const errors = {};
    
    rules.forEach(rule => {
        const field = form.querySelector(`[name="${rule.field}"]`);
        if (field) {
            const value = field.value.trim();
            
            if (rule.required && !value) {
                isValid = false;
                errors[rule.field] = rule.requiredMessage || 'هذا الحقل مطلوب';
            } else if (value && rule.pattern && !rule.pattern.test(value)) {
                isValid = false;
                errors[rule.field] = rule.patternMessage || 'قيمة غير صحيحة';
            } else if (value && rule.minLength && value.length < rule.minLength) {
                isValid = false;
                errors[rule.field] = `يجب أن يكون ${rule.minLength} أحرف على الأقل`;
            } else if (value && rule.maxLength && value.length > rule.maxLength) {
                isValid = false;
                errors[rule.field] = `يجب ألا يتجاوز ${rule.maxLength} حرف`;
            }
        }
    });
    
    // عرض الأخطاء
    Object.keys(errors).forEach(fieldName => {
        const errorElement = document.getElementById(`${fieldName}-error`);
        if (errorElement) {
            errorElement.textContent = errors[fieldName];
            errorElement.style.display = 'block';
        }
    });
    
    return isValid;
}

// مسح أخطاء النموذج
function clearFormErrors(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const errorElements = form.querySelectorAll('.error-message');
    errorElements.forEach(el => {
        el.textContent = '';
        el.style.display = 'none';
    });
}

// ===================== دوال التنقل =====================

// الانتقال إلى صفحة مع تأثير انزلاقي
function navigateTo(url, transition = 'slide') {
    const content = document.querySelector('.content');
    if (content && transition === 'slide') {
        content.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => {
            window.location.href = url;
        }, 300);
    } else {
        window.location.href = url;
    }
}

// الرجوع للصفحة السابقة
function goBack() {
    if (document.referrer && document.referrer.includes(window.location.host)) {
        history.back();
    } else {
        window.location.href = '/';
    }
}

// ===================== تهيئة الصفحة =====================

// إضافة تأثيرات CSS للرسوم المتحركة
function addAnimationStyles() {
    if (!document.querySelector('#animation-styles')) {
        const style = document.createElement('style');
        style.id = 'animation-styles';
        style.textContent = `
            @keyframes slideOut {
                0% { transform: translateX(0); opacity: 1; }
                100% { transform: translateX(-100%); opacity: 0; }
            }
            @keyframes slideIn {
                0% { transform: translateX(100%); opacity: 0; }
                100% { transform: translateX(0); opacity: 1; }
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .fade-in {
                animation: fadeIn 0.5s ease forwards;
            }
            .card, .btn, .faq-item {
                animation: fadeIn 0.4s ease backwards;
            }
        `;
        document.head.appendChild(style);
    }
}

// إضافة عناصر عامة للصفحة
function addGlobalElements() {
    // إضافة عنصر التنبيه العام
    if (!document.getElementById('global-alert')) {
        const alertDiv = document.createElement('div');
        alertDiv.id = 'global-alert';
        alertDiv.className = 'alert';
        alertDiv.style.cssText = 'position: fixed; top: 70px; left: 20px; right: 20px; z-index: 1000; display: none;';
        document.body.appendChild(alertDiv);
    }
    
    // إضافة مؤشر التحميل العام
    if (!document.getElementById('global-loading')) {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'global-loading';
        loadingDiv.className = 'loading';
        loadingDiv.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(loadingDiv);
    }
}

// ===================== دوال المشاركة الاجتماعية =====================

// مشاركة على واتساب
function shareOnWhatsApp(text, url) {
    const shareUrl = `https://wa.me/?text=${encodeURIComponent(text + ' ' + url)}`;
    window.open(shareUrl, '_blank');
}

// مشاركة على فيسبوك
function shareOnFacebook(url) {
    const shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
    window.open(shareUrl, '_blank');
}

// مشاركة على تويتر
function shareOnTwitter(text, url) {
    const shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
    window.open(shareUrl, '_blank');
}

// نسخ الرابط
function copyLink(url) {
    copyToClipboard(url);
}

// ===================== دوال الأسئلة الشائعة =====================

// تحميل الأسئلة الشائعة من API
async function loadFAQs(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    showLoading();
    
    try {
        const faqs = await apiGet('/api/faq');
        container.innerHTML = '';
        
        const colors = ['#1976d2', '#388e3c', '#f57c00', '#7b1fa2', '#c2185b', '#00796b', '#5d4037', '#0288d1'];
        
        faqs.forEach((faq, index) => {
            const faqItem = createElement('div', { className: 'faq-item' });
            const faqBtn = createElement('button', { className: 'faq-btn' }, [
                createElement('i', { className: `fas fa-question-circle`, style: { color: colors[index % colors.length] } }),
                createElement('span', { style: { flex: 1, textAlign: 'right' } }, [faq.question]),
                createElement('i', { className: 'fas fa-chevron-left', style: { color: '#ccc' } })
            ]);
            
            faqBtn.onclick = () => {
                window.location.href = `/faq_detail?q=${encodeURIComponent(faq.question)}&a=${encodeURIComponent(faq.answer)}`;
            };
            
            faqItem.appendChild(faqBtn);
            container.appendChild(faqItem);
        });
    } catch (error) {
        console.error('Error loading FAQs:', error);
        container.innerHTML = '<p class="text-center text-danger">حدث خطأ في تحميل الأسئلة</p>';
    } finally {
        hideLoading();
    }
}

// ===================== تهيئة التطبيق =====================

// تهيئة جميع الوظائف عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // إضافة العناصر العامة
    addGlobalElements();
    addAnimationStyles();
    
    // تهيئة وضع الظلام
    initDarkMode();
    
    // إضافة تأثيرات على الأزرار
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // إضافة تأثير موجة (ripple)
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${e.clientX - rect.left - size/2}px`;
            ripple.style.top = `${e.clientY - rect.top - size/2}px`;
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    // إضافة تأثير hover للبطاقات
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.transition = 'all 0.3s ease';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    console.log('✅ تم تهيئة التطبيق بنجاح');
});

// إضافة تأثير الموجة (ripple) للزر
const style = document.createElement('style');
style.textContent = `
    .btn {
        position: relative;
        overflow: hidden;
    }
    .ripple {
        position: absolute;
        border-radius: 50%;
        background-color: rgba(255, 255, 255, 0.7);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    body.dark-mode {
        background: #1a1a2e;
    }
    body.dark-mode .card {
        background: #16213e;
        color: #eee;
    }
    body.dark-mode .content {
        background: #1a1a2e;
    }
`;
document.head.appendChild(style);

// تصدير الدوال للاستخدام العالمي
window.app = {
    showMessage,
    showLoading,
    hideLoading,
    validateEgyptianPhone,
    validateNationalId,
    validateSeatNumber,
    copyToClipboard,
    compressImage,
    apiGet,
    apiPost,
    saveToLocalStorage,
    getFromLocalStorage,
    toggleDarkMode,
    navigateTo,
    goBack,
    shareOnWhatsApp,
    shareOnFacebook,
    shareOnTwitter,
    copyLink,
    loadFAQs
};