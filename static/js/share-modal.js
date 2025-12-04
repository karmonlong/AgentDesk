// Share Modal JavaScript
// 防止 addEventListener 错误

(function() {
    'use strict';
    
    // 等待 DOM 加载完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initShareModal);
    } else {
        initShareModal();
    }
    
    function initShareModal() {
        // 检查元素是否存在再添加事件监听
        const shareModal = document.getElementById('shareModal');
        const shareButton = document.getElementById('shareButton');
        const shareClose = document.getElementById('shareClose');
        
        if (shareButton) {
            shareButton.addEventListener('click', function() {
                if (shareModal) {
                    shareModal.style.display = 'block';
                }
            });
        }
        
        if (shareClose) {
            shareClose.addEventListener('click', function() {
                if (shareModal) {
                    shareModal.style.display = 'none';
                }
            });
        }
        
        // 点击外部关闭
        if (shareModal) {
            shareModal.addEventListener('click', function(e) {
                if (e.target === shareModal) {
                    shareModal.style.display = 'none';
                }
            });
        }
    }
})();

