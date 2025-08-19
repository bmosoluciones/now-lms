/**
 * PayPal Checkout JavaScript SDK Integration
 * Handles course payment processing with PayPal
 */

// Payment state management
const PaymentState = {
    IDLE: 'idle',
    PROCESSING: 'processing',
    COMPLETED: 'completed',
    FAILED: 'failed'
};

let currentPaymentState = PaymentState.IDLE;

function showPaymentMessage(message, type = 'info') {
    const messageContainer = document.getElementById('payment-messages');
    if (messageContainer) {
        const alertClass = type === 'error' ? 'alert-danger' : 
                          type === 'success' ? 'alert-success' : 'alert-info';
        messageContainer.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    } else {
        // Fallback to alert if container not found
        alert(message);
    }
}

function setPaymentState(state) {
    currentPaymentState = state;
    const container = document.getElementById('paypal-button-container');
    const loadingDiv = document.getElementById('paypal-loading');
    
    switch(state) {
        case PaymentState.PROCESSING:
            if (container) container.style.pointerEvents = 'none';
            showPaymentMessage('Procesando pago...', 'info');
            break;
        case PaymentState.COMPLETED:
            showPaymentMessage('¡Pago completado exitosamente! Redirigiendo...', 'success');
            break;
        case PaymentState.FAILED:
            if (container) container.style.pointerEvents = 'auto';
            break;
        default:
            if (container) container.style.pointerEvents = 'auto';
    }
}

function initializePayPalButtons(courseCode, amount, currency = 'USD') {
    // Check if PayPal SDK is loaded
    if (typeof paypal === 'undefined') {
        console.error('PayPal SDK not loaded');
        showPaymentMessage('Error: PayPal no está disponible. Por favor recargue la página.', 'error');
        return;
    }

    // Validate required parameters
    if (!courseCode || !amount || amount <= 0) {
        console.error('Invalid payment parameters:', { courseCode, amount, currency });
        showPaymentMessage('Error: Parámetros de pago inválidos.', 'error');
        return;
    }

    try {
        paypal.Buttons({
            createOrder: function(data, actions) {
                console.log('Creating PayPal order:', { courseCode, amount, currency });
                setPaymentState(PaymentState.PROCESSING);
                
                return actions.order.create({
                    purchase_units: [{
                        amount: {
                            value: parseFloat(amount).toFixed(2),
                            currency_code: currency
                        },
                        description: `Pago por curso ${courseCode}`,
                        custom_id: `${courseCode}-${Date.now()}`
                    }]
                }).catch(error => {
                    console.error('Error creating PayPal order:', error);
                    setPaymentState(PaymentState.FAILED);
                    showPaymentMessage('Error al crear la orden de pago. Por favor intente nuevamente.', 'error');
                    throw error;
                });
            },
            onApprove: function(data, actions) {
                console.log('PayPal payment approved:', data);
                setPaymentState(PaymentState.PROCESSING);
                
                return actions.order.capture().then(function(details) {
                    console.log('Payment captured:', details);
                    
                    // Send payment confirmation to backend with retry
                    return confirmPaymentWithRetry({
                        orderID: data.orderID,
                        payerID: details.payer.payer_id,
                        courseCode: courseCode,
                        amount: amount,
                        currency: currency
                    }, 3);
                }).catch(error => {
                    console.error('Payment capture failed:', error);
                    setPaymentState(PaymentState.FAILED);
                    showPaymentMessage('Error al capturar el pago. Por favor contacte soporte.', 'error');
                    throw error;
                });
            },
            onError: function(err) {
                console.error("PayPal error:", err);
                setPaymentState(PaymentState.FAILED);
                showPaymentMessage('Error de PayPal: ' + (err.message || 'Error desconocido'), 'error');
            },
            onCancel: function(data) {
                console.log('Payment cancelled by user:', data);
                setPaymentState(PaymentState.IDLE);
                showPaymentMessage('Pago cancelado por el usuario.', 'info');
            }
        }).render('#paypal-button-container').then(function() {
            console.log('PayPal buttons rendered successfully');
            // Hide loading indicator
            const loadingDiv = document.getElementById('paypal-loading');
            if (loadingDiv) {
                loadingDiv.style.display = 'none';
            }
        }).catch(function(error) {
            console.error('Error rendering PayPal buttons:', error);
            showPaymentMessage('Error al cargar los botones de PayPal. Por favor recargue la página.', 'error');
        });
    } catch (error) {
        console.error('Error initializing PayPal buttons:', error);
        setPaymentState(PaymentState.FAILED);
        showPaymentMessage('Error al inicializar PayPal. Por favor recargue la página.', 'error');
    }
}

async function confirmPaymentWithRetry(paymentData, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            console.log(`Payment confirmation attempt ${attempt}/${maxRetries}`);
            
            const response = await fetch('/paypal_checkout/confirm_payment', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(paymentData)
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const result = await response.json();
            
            if (result.success) {
                setPaymentState(PaymentState.COMPLETED);
                // Redirect after a short delay to show success message
                setTimeout(() => {
                    window.location.href = result.redirect_url || `/course/${paymentData.courseCode}/take`;
                }, 2000);
                return result;
            } else {
                throw new Error(result.error || 'Payment processing failed');
            }
            
        } catch (error) {
            console.error(`Payment confirmation attempt ${attempt} failed:`, error);
            
            if (attempt === maxRetries) {
                setPaymentState(PaymentState.FAILED);
                showPaymentMessage(
                    `Error al confirmar el pago después de ${maxRetries} intentos. ` +
                    `Por favor contacte soporte con el ID de orden: ${paymentData.orderID}`,
                    'error'
                );
                throw error;
            }
            
            // Wait before retry (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        }
    }
}

function getCSRFToken() {
    // Get CSRF token from meta tag (primary method)
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        const token = metaToken.getAttribute('content');
        if (token && token.trim() !== '') {
            console.log('Using CSRF token from meta tag');
            return token;
        }
    }
    
    // Fallback 1: get from hidden form field
    const hiddenInput = document.querySelector('input[name="csrf_token"]');
    if (hiddenInput) {
        const token = hiddenInput.value;
        if (token && token.trim() !== '') {
            console.log('Using CSRF token from hidden input');
            return token;
        }
    }
    
    // Fallback 2: try to get from any form on the page
    const anyForm = document.querySelector('form input[name="csrf_token"]');
    if (anyForm) {
        const token = anyForm.value;
        if (token && token.trim() !== '') {
            console.log('Using CSRF token from form');
            return token;
        }
    }
    
    // Fallback 3: generate a warning and try to continue without CSRF
    console.warn('No CSRF token found - this may cause payment confirmation to fail');
    return '';
}

// Enhanced PayPal SDK loading with retry mechanism
function loadPayPalSDKWithRetry(clientId, currency, maxRetries = 3) {
    return new Promise((resolve, reject) => {
        let attempt = 0;
        
        function tryLoad() {
            attempt++;
            console.log(`Loading PayPal SDK attempt ${attempt}/${maxRetries}`);
            
            const script = document.createElement('script');
            script.src = `https://www.paypal.com/sdk/js?client-id=${clientId}&currency=${currency}`;
            
            script.onload = function() {
                console.log('PayPal SDK loaded successfully');
                document.dispatchEvent(new CustomEvent('paypal-loaded'));
                resolve();
            };
            
            script.onerror = function(error) {
                console.error(`PayPal SDK loading attempt ${attempt} failed:`, error);
                
                if (attempt < maxRetries) {
                    // Remove failed script
                    if (script.parentNode) {
                        script.parentNode.removeChild(script);
                    }
                    
                    // Retry after delay (exponential backoff)
                    setTimeout(tryLoad, Math.pow(2, attempt) * 1000);
                } else {
                    reject(new Error('Failed to load PayPal SDK after ' + maxRetries + ' attempts'));
                }
            };
            
            document.head.appendChild(script);
        }
        
        tryLoad();
    });
}

// Initialize PayPal buttons when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const paypalContainer = document.getElementById('paypal-button-container');
    if (paypalContainer) {
        const courseCode = paypalContainer.dataset.courseCode;
        const amount = parseFloat(paypalContainer.dataset.amount);
        const currency = paypalContainer.dataset.currency || 'USD';
        
        if (courseCode && amount && amount > 0) {
            // Wait for PayPal loaded event before initializing buttons
            document.addEventListener('paypal-loaded', function() {
                setTimeout(() => {
                    initializePayPalButtons(courseCode, amount, currency);
                }, 100); // Small delay to ensure DOM is ready
            });
        } else {
            showPaymentMessage('Error: Datos del curso inválidos.', 'error');
        }
    }
});

// Prevent multiple submissions and handle browser back/forward
window.addEventListener('beforeunload', function(e) {
    if (currentPaymentState === PaymentState.PROCESSING) {
        e.preventDefault();
        e.returnValue = 'Un pago está siendo procesado. ¿Está seguro de que desea salir?';
        return e.returnValue;
    }
});

// Handle page visibility changes (tab switching)
document.addEventListener('visibilitychange', function() {
    if (document.hidden && currentPaymentState === PaymentState.PROCESSING) {
        console.log('Page hidden during payment processing');
    } else if (!document.hidden && currentPaymentState === PaymentState.PROCESSING) {
        console.log('Page visible again - payment may still be processing');
        showPaymentMessage('Verificando estado del pago...', 'info');
    }
});