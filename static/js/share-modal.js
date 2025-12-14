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
        // 额外兜底：任何异常都不影响主页面其它脚本（比如 AlphaFund 图表渲染）
        try {
            // 检查元素是否存在再添加事件监听
            const shareModal = document.getElementById('shareModal');
            const shareButton = document.getElementById('shareButton');
            const shareClose = document.getElementById('shareClose');
            
            if (shareButton && typeof shareButton.addEventListener === 'function') {
                shareButton.addEventListener('click', function() {
                    if (shareModal) {
                        shareModal.style.display = 'block';
                    }
                });
            }
            
            if (shareClose && typeof shareClose.addEventListener === 'function') {
                shareClose.addEventListener('click', function() {
                    if (shareModal) {
                        shareModal.style.display = 'none';
                    }
                });
            }
            
            // 点击外部关闭
            if (shareModal && typeof shareModal.addEventListener === 'function') {
                shareModal.addEventListener('click', function(e) {
                    if (e.target === shareModal) {
                        shareModal.style.display = 'none';
                    }
                });
            }
        } catch (e) {
            // 静默失败：分享弹窗不影响主流程
        }
    }
})();










