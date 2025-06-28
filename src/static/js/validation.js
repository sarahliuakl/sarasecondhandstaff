/**
 * 共享验证函数库
 * 用于邮箱和新西兰手机号码验证
 */

// 邮箱验证正则表达式
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

// 新西兰手机号码验证正则表达式
// 支持格式: 020xxxxxxx, 021xxxxxxx, 022xxxxxxx, 027xxxxxxx, 028xxxxxxxx, 029xxxxxxxx
const NZ_MOBILE_REGEX = /^0(20|21|22|27|28|29)\d{6,8}$/;

// 新西兰手机号码格式化显示正则 (带空格或短划线)
const NZ_MOBILE_FORMATTED_REGEX = /^0(20|21|22|27|28|29)[\s-]?\d{3}[\s-]?\d{3,4}$/;

/**
 * 验证邮箱地址格式
 * @param {string} email - 待验证的邮箱地址
 * @returns {boolean} - 验证结果
 */
function validateEmail(email) {
    if (!email || typeof email !== 'string') {
        return false;
    }
    return EMAIL_REGEX.test(email.trim());
}

/**
 * 验证新西兰手机号码格式
 * @param {string} phone - 待验证的手机号码
 * @returns {boolean} - 验证结果
 */
function validateNZMobile(phone) {
    if (!phone || typeof phone !== 'string') {
        return false;
    }
    
    // 清理输入：移除空格、短划线、括号等
    const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
    
    // 验证清理后的号码
    return NZ_MOBILE_REGEX.test(cleanPhone);
}

/**
 * 判断输入是邮箱还是电话号码
 * @param {string} input - 待判断的输入
 * @returns {string} - 'email' | 'phone' | 'invalid'
 */
function detectInputType(input) {
    if (!input || typeof input !== 'string') {
        return 'invalid';
    }
    
    const trimmedInput = input.trim();
    
    // 如果包含@符号，判定为邮箱
    if (trimmedInput.includes('@')) {
        return 'email';
    }
    
    // 如果不包含@且包含数字，判定为电话号码
    if (/\d/.test(trimmedInput)) {
        return 'phone';
    }
    
    return 'invalid';
}

/**
 * 综合验证邮箱或手机号码
 * @param {string} input - 待验证的输入
 * @returns {object} - 验证结果对象 {isValid: boolean, type: string, message: string}
 */
function validateEmailOrPhone(input) {
    if (!input || typeof input !== 'string') {
        return {
            isValid: false,
            type: 'invalid',
            message: 'Please enter email address or phone number'
        };
    }
    
    const trimmedInput = input.trim();
    const inputType = detectInputType(trimmedInput);
    
    switch (inputType) {
        case 'email':
            if (validateEmail(trimmedInput)) {
                return {
                    isValid: true,
                    type: 'email',
                    message: 'Valid email format'
                };
            } else {
                return {
                    isValid: false,
                    type: 'email',
                    message: 'Please enter a valid email address (e.g: example@email.com)'
                };
            }
            
        case 'phone':
            if (validateNZMobile(trimmedInput)) {
                return {
                    isValid: true,
                    type: 'phone',
                    message: 'Valid NZ mobile number'
                };
            } else {
                return {
                    isValid: false,
                    type: 'phone',
                    message: 'Please enter a valid New Zealand mobile number (e.g: 021234567)'
                };
            }
            
        default:
            return {
                isValid: false,
                type: 'invalid',
                message: 'Please enter a valid email address or New Zealand mobile number'
            };
    }
}

/**
 * 格式化新西兰手机号码显示
 * @param {string} phone - 手机号码
 * @returns {string} - 格式化后的号码
 */
function formatNZMobile(phone) {
    if (!phone || typeof phone !== 'string') {
        return phone;
    }
    
    const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
    
    if (!NZ_MOBILE_REGEX.test(cleanPhone)) {
        return phone; // 如果格式不正确，返回原始输入
    }
    
    // 根据号码长度进行格式化
    if (cleanPhone.length === 10) {
        // 例如: 0212345678 -> 021 234 567
        return cleanPhone.replace(/^(\d{3})(\d{3})(\d{4})$/, '$1 $2 $3');
    } else if (cleanPhone.length === 9) {
        // 例如: 021234567 -> 021 234 567  
        return cleanPhone.replace(/^(\d{3})(\d{3})(\d{3})$/, '$1 $2 $3');
    } else if (cleanPhone.length === 8) {
        // 例如: 02123456 -> 021 234 56
        return cleanPhone.replace(/^(\d{3})(\d{3})(\d{2})$/, '$1 $2 $3');
    }
    
    return cleanPhone;
}

/**
 * 实时验证输入框内容并显示反馈
 * @param {HTMLElement} inputElement - 输入框元素
 * @param {HTMLElement} feedbackElement - 反馈信息显示元素 (可选)
 * @param {function} callback - 验证完成后的回调函数 (可选)
 */
function setupRealTimeValidation(inputElement, feedbackElement = null, callback = null) {
    if (!inputElement) {
        console.error('输入框元素不能为空');
        return;
    }
    
    function validateInput() {
        const value = inputElement.value;
        const result = validateEmailOrPhone(value);
        
        // 更新输入框样式
        inputElement.classList.remove('border-red-500', 'border-green-500', 'border-gray-300');
        
        if (value.trim() === '') {
            inputElement.classList.add('border-gray-300');
        } else if (result.isValid) {
            inputElement.classList.add('border-green-500');
        } else {
            inputElement.classList.add('border-red-500');
        }
        
        // 更新反馈信息
        if (feedbackElement) {
            feedbackElement.textContent = value.trim() === '' ? '' : result.message;
            feedbackElement.className = result.isValid ? 'text-green-600 text-sm mt-1' : 'text-red-600 text-sm mt-1';
        }
        
        // 执行回调
        if (callback && typeof callback === 'function') {
            callback(result);
        }
        
        return result;
    }
    
    // 绑定事件监听器
    inputElement.addEventListener('input', validateInput);
    inputElement.addEventListener('blur', validateInput);
    
    // 返回验证函数，以便外部调用
    return validateInput;
}

/**
 * 为表单添加提交前验证
 * @param {HTMLFormElement} formElement - 表单元素
 * @param {string} inputSelector - 需要验证的输入框选择器
 * @param {string} errorMessage - 验证失败时的错误信息 (可选)
 */
function setupFormValidation(formElement, inputSelector, errorMessage = 'Please enter a valid email address or New Zealand mobile number') {
    if (!formElement) {
        console.error('表单元素不能为空');
        return;
    }
    
    formElement.addEventListener('submit', function(event) {
        const inputElement = formElement.querySelector(inputSelector);
        
        if (!inputElement) {
            console.error('找不到输入框元素:', inputSelector);
            return;
        }
        
        const result = validateEmailOrPhone(inputElement.value);
        
        if (!result.isValid) {
            event.preventDefault();
            alert(errorMessage + '\n' + result.message);
            inputElement.focus();
            return false;
        }
        
        return true;
    });
}

// 导出函数 (如果使用模块系统)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        validateEmail,
        validateNZMobile,
        detectInputType,
        validateEmailOrPhone,
        formatNZMobile,
        setupRealTimeValidation,
        setupFormValidation
    };
}