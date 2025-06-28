/**
 * Beautiful toast notification system
 * 美观的提示系统
 */

// Toast 容器样式
const TOAST_STYLES = {
    container: `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        pointer-events: none;
    `,
    toast: `
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        min-width: 300px;
        max-width: 400px;
        pointer-events: auto;
        transform: translateX(100%);
        opacity: 0;
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
    `,
    success: `
        border-left: 4px solid #10b981;
        color: #065f46;
    `,
    error: `
        border-left: 4px solid #ef4444;
        color: #991b1b;
    `,
    warning: `
        border-left: 4px solid #f59e0b;
        color: #92400e;
    `,
    info: `
        border-left: 4px solid #3b82f6;
        color: #1e40af;
    `,
    icon: `
        display: inline-block;
        margin-right: 8px;
        font-size: 16px;
    `,
    title: `
        font-weight: 600;
        margin-bottom: 4px;
        font-size: 14px;
    `,
    message: `
        font-size: 13px;
        line-height: 1.4;
        opacity: 0.9;
    `,
    closeButton: `
        position: absolute;
        top: 8px;
        right: 8px;
        background: none;
        border: none;
        font-size: 18px;
        cursor: pointer;
        opacity: 0.5;
        transition: opacity 0.2s;
        padding: 4px;
        border-radius: 4px;
    `
};

// Toast 图标映射
const TOAST_ICONS = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
};

// 创建 Toast 容器
function createToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = TOAST_STYLES.container;
        document.body.appendChild(container);
    }
    return container;
}

// 应用内联样式
function applyStyles(element, ...styles) {
    const combinedStyles = styles.join(' ');
    element.style.cssText = combinedStyles;
}

/**
 * 显示 Toast 提示
 * @param {string} message - 提示消息
 * @param {string} type - 提示类型: success, error, warning, info
 * @param {string} title - 提示标题 (可选)
 * @param {number} duration - 显示时长，毫秒 (默认 5000)
 */
function showToast(message, type = 'info', title = '', duration = 5000) {
    const container = createToastContainer();
    
    // 创建 toast 元素
    const toast = document.createElement('div');
    const icon = TOAST_ICONS[type] || TOAST_ICONS.info;
    
    // 构建内容
    let content = `
        <div style="${TOAST_STYLES.icon}">${icon}</div>
        <div style="flex: 1;">
    `;
    
    if (title) {
        content += `<div style="${TOAST_STYLES.title}">${title}</div>`;
    }
    
    content += `
            <div style="${TOAST_STYLES.message}">${message}</div>
        </div>
        <button style="${TOAST_STYLES.closeButton}" onclick="this.closest('[data-toast]').remove()">×</button>
    `;
    
    toast.innerHTML = content;
    toast.setAttribute('data-toast', 'true');
    
    // 应用样式
    applyStyles(toast, 
        TOAST_STYLES.toast, 
        TOAST_STYLES[type] || TOAST_STYLES.info
    );
    
    // 设置 flex 布局
    toast.style.display = 'flex';
    toast.style.alignItems = 'flex-start';
    
    // 添加到容器
    container.appendChild(toast);
    
    // 动画显示
    requestAnimationFrame(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity = '1';
    });
    
    // 自动关闭
    if (duration > 0) {
        setTimeout(() => {
            hideToast(toast);
        }, duration);
    }
    
    // 悬停时暂停自动关闭
    let autoCloseTimer;
    if (duration > 0) {
        autoCloseTimer = setTimeout(() => hideToast(toast), duration);
        
        toast.addEventListener('mouseenter', () => {
            clearTimeout(autoCloseTimer);
        });
        
        toast.addEventListener('mouseleave', () => {
            autoCloseTimer = setTimeout(() => hideToast(toast), 2000);
        });
    }
    
    return toast;
}

/**
 * 隐藏 Toast
 * @param {HTMLElement} toast - Toast 元素
 */
function hideToast(toast) {
    if (!toast || !toast.parentNode) return;
    
    toast.style.transform = 'translateX(100%)';
    toast.style.opacity = '0';
    
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

/**
 * 显示成功提示
 * @param {string} message - 提示消息
 * @param {string} title - 提示标题 (可选)
 * @param {number} duration - 显示时长 (可选)
 */
function showSuccess(message, title = 'Success', duration = 4000) {
    return showToast(message, 'success', title, duration);
}

/**
 * 显示错误提示
 * @param {string} message - 提示消息
 * @param {string} title - 提示标题 (可选)
 * @param {number} duration - 显示时长 (可选)
 */
function showError(message, title = 'Error', duration = 6000) {
    return showToast(message, 'error', title, duration);
}

/**
 * 显示警告提示
 * @param {string} message - 提示消息
 * @param {string} title - 提示标题 (可选)
 * @param {number} duration - 显示时长 (可选)
 */
function showWarning(message, title = 'Warning', duration = 5000) {
    return showToast(message, 'warning', title, duration);
}

/**
 * 显示信息提示
 * @param {string} message - 提示消息
 * @param {string} title - 提示标题 (可选)
 * @param {number} duration - 显示时长 (可选)
 */
function showInfo(message, title = 'Info', duration = 4000) {
    return showToast(message, 'info', title, duration);
}

/**
 * 清除所有 Toast
 */
function clearAllToasts() {
    const container = document.getElementById('toast-container');
    if (container) {
        const toasts = container.querySelectorAll('[data-toast]');
        toasts.forEach(toast => hideToast(toast));
    }
}

// 表单验证专用函数
function showValidationError(message, fieldName = '') {
    const title = fieldName ? `${fieldName} Error` : 'Validation Error';
    return showError(message, title, 6000);
}

// 导出函数 (如果使用模块系统)
if (typeof window !== 'undefined') {
    window.showToast = showToast;
    window.showSuccess = showSuccess;
    window.showError = showError;
    window.showWarning = showWarning;
    window.showInfo = showInfo;
    window.clearAllToasts = clearAllToasts;
    window.showValidationError = showValidationError;
}