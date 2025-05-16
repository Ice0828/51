// 主JavaScript文件

// 在页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 处理闪现消息的淡出效果
    const flashMessages = document.querySelectorAll('.flash-message');
    
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            // 3秒后淡出消息
            setTimeout(() => {
                message.style.opacity = '1';
                
                // 淡出动画
                const fadeOut = setInterval(() => {
                    if (message.style.opacity > 0) {
                        message.style.opacity -= 0.1;
                    } else {
                        clearInterval(fadeOut);
                        message.style.display = 'none';
                    }
                }, 50);
            }, 3000);
        });
    }
    
    // 手机屏幕下的导航菜单切换
    const navLinks = document.querySelector('.nav-links');
    const logo = document.querySelector('.logo');
    
    if (logo && navLinks) {
        logo.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                if (navLinks.style.display === 'flex' || navLinks.style.display === '') {
                    navLinks.style.display = 'none';
                } else {
                    navLinks.style.display = 'flex';
                }
            }
        });
        
        // 窗口大小变化时重置导航栏样式
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                navLinks.style.display = 'flex';
            }
        });
    }
}); 